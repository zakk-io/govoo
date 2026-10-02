/** @odoo-module **/

import { Component, useState, useRef, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { user } from "@web/core/user";
import { formatAiText } from "./ai_text_formatter";

// Real, grounded-Q&A-shaped questions (AI-F09) -- deliberately not generic
// placeholders like "Generate report" / "Summarize data", which this
// feature cluster does not do (retrieval + narrative synthesis with
// citations, nothing else).
const SUGGESTED_QUESTIONS = [
    _t("What compliance filings are due this month?"),
    _t("Which resolutions are still open?"),
    _t("When is our next board meeting?"),
];

/**
 * Persistent floating entry point for AI-F09 Governance Q&A.
 *
 * Gated to backend-only (registered on "main_components", never
 * website.layout) and to users in govoo_ai.group_govoo_ai_user -- the icon
 * itself does not render for anyone else, rather than rendering and then
 * failing on click.
 */
export class AiChatWidget extends Component {
    static template = "govoo_ai.AiChatWidget";
    static props = {};

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.messagesRef = useRef("messages");
        this.inputRef = useRef("input");

        this.state = useState({
            visible: false,
            open: false,
            loading: false,
            messages: [],
            input: "",
        });
        this.suggestedQuestions = SUGGESTED_QUESTIONS;

        onWillStart(async () => {
            this.state.visible = await user.hasGroup("govoo_ai.group_govoo_ai_user");
        });
    }

    async onIconClick() {
        if (this.state.open) {
            this.state.open = false;
            return;
        }
        let config;
        try {
            config = await this.orm.call("govoo.ai.qa", "get_widget_config", []);
        } catch {
            this.notification.add(_t("Could not reach the AI service. Please try again."), {
                type: "danger",
            });
            return;
        }
        if (!config.configured) {
            if (config.can_configure) {
                this.action.doAction("govoo_ai.action_govoo_ai_config");
            } else {
                this.notification.add(
                    _t(
                        "Governance Q&A is not enabled for your company yet. " +
                            "Contact your AI Administrator."
                    ),
                    { type: "warning" }
                );
            }
            return;
        }
        this.state.open = true;
        await this.focusInputNextTick();
    }

    closeChat() {
        this.state.open = false;
    }

    onChipClick(question) {
        this.state.input = question;
        this.sendMessage();
    }

    onInputKeydown(ev) {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            this.sendMessage();
        }
    }

    formatText(text) {
        return formatAiText(text);
    }

    async sendMessage() {
        const text = this.state.input.trim();
        if (!text || this.state.loading) {
            return;
        }
        this.state.input = "";
        // History sent to the backend excludes the turn we're about to add
        // (it's the new question, not prior context) and is trimmed
        // server-side regardless of what's sent here.
        const history = this.state.messages.map((message) => ({
            role: message.role,
            content: message.text,
        }));
        this.state.messages.push({ role: "user", text });
        this.state.loading = true;
        await this.scrollToBottomNextTick();
        try {
            const result = await this.orm.call("govoo.ai.qa", "run_for_widget", [text, history]);
            this.state.messages.push({
                role: "assistant",
                text: result.answer,
                found: result.found,
                citations: result.citations || [],
            });
        } catch {
            this.state.messages.push({
                role: "assistant",
                text: _t("Something went wrong answering that question. Please try again."),
                found: false,
                citations: [],
            });
        } finally {
            this.state.loading = false;
            await this.scrollToBottomNextTick();
        }
    }

    async openCitation(citation) {
        const action = await this.orm.call("govoo.ai.suggestion", "action_open_target", [
            [citation.suggestion_id],
        ]);
        this.action.doAction(action);
    }

    async scrollToBottomNextTick() {
        await new Promise(requestAnimationFrame);
        const el = this.messagesRef.el;
        if (el) {
            el.scrollTop = el.scrollHeight;
        }
    }

    async focusInputNextTick() {
        await new Promise(requestAnimationFrame);
        this.inputRef.el?.focus();
    }
}

registry.category("main_components").add("govoo_ai.AiChatWidget", {
    Component: AiChatWidget,
});
