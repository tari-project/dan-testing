//  Copyright 2022. The Tari Project
//
//  Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
//  following conditions are met:
//
//  1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following
//  disclaimer.
//
//  2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
//  following disclaimer in the documentation and/or other materials provided with the distribution.
//
//  3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote
//  products derived from this software without specific prior written permission.
//
//  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
//  INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
//  DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
//  SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
//  SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
//  WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
//  USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import "./Substates.css";
import {StyledPaper} from "../../components/StyledComponents";
import Grid from "@mui/material/Grid";
import SecondaryHeading from "../../components/SecondaryHeading";
import {useState, useEffect} from "react";
import {Error} from "@mui/icons-material";
import {getSubstate, listSubstates} from "../../wallet.ts";
import {Alert, CircularProgress} from "@mui/material";
import {Settings} from "../home/SettingsForm.tsx";

import {SubstatesGetResponse} from "@tariproject/wallet_jrpc_client";
import useTariProvider from "../../store/provider.ts";
import useSettings from "../../store/settings.ts";

function Substates() {
    const {provider} = useTariProvider();
    const {settings} = useSettings();

    const [error, setError] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [components, setComponents] = useState<string[]>([]);
    const [selectedComponent, setSelectedComponent] = useState<string | null>(
        null
    );
    const [
        loadedComponent,
        setLoadedComponent
    ] = useState<SubstatesGetResponse | null>(null);

    useEffect(() => {
        if (settings) {
            listSubstates(provider, settings.template, "Component")
                .then(substates => {
                    setComponents(
                        substates
                            .filter(s => !!s.substate_id.Component)
                            .map(s => s.substate_id.Component)
                    );
                    setIsLoading(false);
                })
                .catch(e => {
                    setError(e.message);
                });
        }
    }, [settings]);

    useEffect(() => {
        if (selectedComponent && provider) {
            getSubstate(provider, selectedComponent).then(
                substate => {
                    // TODO: fix interface for tarijs
                    setLoadedComponent(substate as SubstatesGetResponse | null);
                }
            );
        } else {
            setSelectedComponent(components.length > 0 ? components[0] : null);
        }
    }, [components, selectedComponent, settings, provider]);

    if (isLoading || !settings) {
        return (
            <>
                <Grid item sm={12} md={12} xs={12}>
                    <SecondaryHeading>Components</SecondaryHeading>
                </Grid>
                <Grid item xs={12} md={12} lg={12}>
                    {error && (
                        <Alert icon={<Error/>} severity="error">
                            {error}
                        </Alert>
                    )}
                    <StyledPaper>
                        <CircularProgress/>
                    </StyledPaper>
                </Grid>
                <Grid item xs={12} md={12} lg={12}>
                    <CircularProgress/>
                </Grid>
            </>
        );
    }
    return (
        <>
            <Grid item sm={12} md={12} xs={12}>
                <SecondaryHeading>Components</SecondaryHeading>
            </Grid>
            <Grid item xs={12} md={12} lg={12}>
                {error && (
                    <Alert icon={<Error/>} severity="error">
                        {error}
                    </Alert>
                )}
                <StyledPaper>
          <pre>
            {loadedComponent && JSON.stringify(loadedComponent.value, null, 2)}
          </pre>
                </StyledPaper>
            </Grid>
        </>
    );
}

export default Substates;
