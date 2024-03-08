import {Settings} from "./routes/home/SettingsForm.tsx";

import {
    FunctionDef,
    SubstatesListRequest,
    SubstatesGetRequest,
    TransactionGetResultResponse,
    Instruction,
    SubstateType,
    SubstateId,
    Arg,
    WalletDaemonClient,
} from "@tariproject/wallet_jrpc_client";


import {providers} from '@tariproject/tarijs';
import {TariProvider} from "@tariproject/tarijs/dist/providers";

const {
    TariProvider,
    metamask: {MetamaskTariProvider},
    walletDaemon: {WalletDaemonTariProvider},
    types: {
        SubstateRequirement,
        TransactionSubmitRequest,
        TransactionStatus
    }
} = providers;

function createClient(url: string) {
    return WalletDaemonClient.usingFetchTransport(url);
}

export async function getTemplateDefinition<T extends TariProvider>(
    provider: T,
    template_address: string
) {
    const resp = await provider.getTemplateDefinition(template_address);
    return resp.template_definition;
}

export async function listSubstates<T extends TariProvider>(
    provider: T,
    template: string | null,
    substateType: SubstateType | null
) {
    if (provider.providerName !== "WalletDaemon") {
        throw new Error(`Unsupported provider ${provider.providerName}`);
    }
    const substates = await (provider as WalletDaemonTariProvider).listSubstates(
        template,
        substateType
    );
    return substates;
}

export async function createFreeTestCoins<T extends TariProvider>(provider: T) {
    console.log("createFreeTestCoins", provider.providerName);
    switch (provider.providerName) {
        case "WalletDaemon":
            const walletProvider = provider as WalletDaemonTariProvider;
            await walletProvider.createFreeTestCoins();
            break;
        case "Metamask":
            const metamaskProvider = provider as MetamaskTariProvider;
            await metamaskProvider.createFreeTestCoins(0);
            break;
        default:
            throw new Error(`Unsupported provider: ${provider.providerName}`);
    }
}

export async function getSubstate<T extends TariProvider>(provider: T, substateId: string) {
    const resp = await provider.getSubstate(substateId);
    return resp;
}

async function authorizeClient(client: WalletDaemonClient) {
    // TODO: keep this token in local storage
    const token = await client.authRequest(["Admin"]);
    await client.authAccept(token, "web");
}

export async function buildInstructionsAndSubmit(
    provider: TariProvider,
    settings: Settings,
    selectedBadge: string | null,
    selectedComponent: string | null,
    func: FunctionDef,
    args: object
) {
    const req = await createTransactionRequest(
        provider,
        settings,
        selectedBadge,
        selectedComponent,
        func,
        args
    );

    const resp = await provider.submitTransaction(req);

    let result = await waitForTransactionResult(provider, resp.transaction_id);

    return result;
}

async function waitForTransactionResult(provider: TariProvider, transactionId: string) {
    while (true) {
        const resp = await provider.getTransactionResult(transactionId);
        const FINALIZED_STATUSES = [
            TransactionStatus.Accepted,
            TransactionStatus.Rejected,
            TransactionStatus.InvalidTransaction,
            TransactionStatus.OnlyFeeAccepted,
            TransactionStatus.DryRun
        ];

        if (resp.status == TransactionStatus.Rejected) {
            throw new Error(`Transaction rejected: ${JSON.stringify(resp.result)}`);
        }

        if (FINALIZED_STATUSES.includes(resp.status)) {
            return resp;
        }
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
}

export async function createTransactionRequest(
    provider: TariProvider,
    settings: Settings,
    selectedBadge: string | null,
    selectedComponent: string | null,
    func: FunctionDef,
    formValues: object
): Promise<TransactionSubmitRequest> {
    const fee = 2000;
    const account = await provider.getAccount();

    const fee_instructions = [
        {
            CallMethod: {
                component_address: account.address,
                method: "pay_fee",
                args: [`Amount(${fee})`]
            }
        }
    ];

    const args = Object.values(formValues) as Arg[];
    const isMethod =
        func.arguments.length > 0 && func.arguments[0].name === "self";

    if (!isMethod && !settings.template) {
        throw new Error("Template not set");
    }

    if (isMethod && !selectedComponent) {
        throw new Error("This call requires a component to be selected");
    }

    let bucketId = 0;

    const proofInstructions: Instruction[] =
        isMethod && selectedBadge
            ? [
                {
                    CallMethod: {
                        component_address: account.address,
                        method: "create_proof_for_resource",
                        args: [selectedBadge]
                    }
                },
                {
                    PutLastInstructionOutputOnWorkspace: {key: [bucketId++]}
                }
            ] as Instruction[]
            : [];

    const callInstruction = isMethod
        ? {
            CallMethod: {
                component_address: selectedComponent,
                method: func.name,
                args: args
            }
        } as Instruction
        : {
            CallFunction: {
                template_address: settings.template,
                function: func.name,
                args: args
            }
        } as Instruction;

    const nextInstructions: Instruction[] =
        func.output.Other?.name === "Bucket"
            ? [
                {PutLastInstructionOutputOnWorkspace: {key: [bucketId]}},
                {
                    CallMethod: {
                        component_address: account.address,
                        method: "deposit",
                        args: [{Workspace: [bucketId]}]
                    }
                }
            ] as Instruction[]
            : [];

    const instructions: Instruction[] = [
        ...proofInstructions,
        callInstruction,
        ...nextInstructions,
        "DropAllProofsInWorkspace" as Instruction
    ];

    const required_substates = [
        {substate_id: account.address, version: null}
    ]

    if (selectedComponent) {
        required_substates.push({substate_id: selectedComponent, version: null});
    }

    return {
        account_id: account.account_id,
        fee_instructions,
        instructions,
        inputs: [],
        input_refs: [],
        override_inputs: false,
        required_substates,
        is_dry_run: false,
        min_epoch: null,
        max_epoch: null
    };
}
