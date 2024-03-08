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

import "./Home.css";
import Button from "@mui/material/Button";
import {FormLabel, TextField} from "@mui/material";
import {useState} from "react";
import Grid from "@mui/material/Grid";
import useSettings from "../../store/settings.ts";

interface Props {
    settings: Settings | null;
    onSave: (settings: Settings) => void;
}

export interface Settings {
    template: string | null;
}


function SettingsForm(props: Props) {
    const {settings, setSettings} = useSettings();

    const [currentSettings, setCurrentSettings] = useState(settings);

    return (
        <form
            onSubmit={evt => {
                evt.preventDefault();
                setSettings(currentSettings);
            }}
        >
            <Grid item xs={12} md={12} lg={12}>
                <FormLabel htmlFor="template">Template ID</FormLabel>
                <TextField
                    id="template"
                    name="template ID"
                    placeholder="Template ID"
                    onChange={evt =>
                        setCurrentSettings({
                            ...currentSettings,
                            template: evt.target.value
                        })
                    }
                    value={currentSettings.template || ""}
                />
            </Grid>
            <Grid item xs={12} md={12} lg={12}>
                <Button type="submit" disabled={settings === currentSettings}>
                    Save
                </Button>
            </Grid>
        </form>
    );
}

export default SettingsForm;
