import {Many2XAutocomplete} from "@web/views/fields/relational_utils";
import {_t} from "@web/core/l10n/translation";
import {patch} from "@web/core/utils/patch";
import {session} from "@web/session";
import {sprintf} from "@web/core/utils/strings";

export function is_option_set(option) {
    if (option === undefined) return false;
    if (typeof option === "string") return option === "true" || option === "True";
    if (typeof option === "boolean") return option;
    return false;
}

patch(Many2XAutocomplete.prototype, {
    setup() {
        super.setup();
        this.ir_options = session.access_control;
    },

    async loadOptionsSource(request) {
        if (this.lastProm) {
            this.lastProm.abort(false);
        }
        if (!(this.ir_options["access_control.limit"] === undefined)) {
            this.props.searchLimit = parseInt(
                this.ir_options["access_control.limit"],
                10
            );
            this.limit = this.props.searchLimit;
        }

        if (typeof this.props.nodeOptions.limit === "number") {
            this.props.searchLimit = this.props.nodeOptions.limit;
            this.limit = this.props.searchLimit;
        }

        this.field_color = this.props.nodeOptions.field_color;
        this.colors = this.props.nodeOptions.colors;

        this.lastProm = this.orm.call(this.props.resModel, "name_search", [], {
            name: request,
            operator: "ilike",
            args: this.props.getDomain(),
            limit: this.props.searchLimit + 1,
            context: this.props.context,
        });
        const records = await this.lastProm;

        var options = records.map((result) => ({
            value: result[0],
            id: result[0],
            label: result[1].split("\n")[0],
        }));

        if (this.limit) {
            options = options.slice(0, this.props.searchLimit);
        }

        if (this.colors && this.field_color) {
            var value_ids = options.map((result) => result.value);
            const objects = await this.orm.call(
                this.props.resModel,
                "search_read",
                [],
                {
                    domain: [["id", "in", value_ids]],
                    fields: [this.field_color],
                }
            );
            for (var index in objects) {
                for (var index_value in options) {
                    if (options[index_value].id === objects[index].id) {
                        // Find value in values by comparing ids
                        var option = options[index_value];
                        // Find color with field value as key
                        var color =
                            this.colors[objects[index][this.field_color]] || "black";
                        option.style = "color:" + color;
                        break;
                    }
                }
            }
        }

        var create_enabled =
            this.props.quickCreate && !this.props.nodeOptions.no_create;

        var raw_result = Object.values(records).map((x) => {
            return x[1];
        });
        var quick_create = is_option_set(this.props.nodeOptions.create),
            quick_create_undef = this.props.nodeOptions.create === undefined,
            access_control_create_undef = this.ir_options["access_control.create"] === undefined,
            access_control_create = is_option_set(this.ir_options["access_control.create"]);
        var show_create =
            (!this.props.nodeOptions && (access_control_create_undef || access_control_create)) ||
            (this.props.nodeOptions &&
                (quick_create ||
                    (quick_create_undef && (access_control_create_undef || access_control_create))));
        if (
            create_enabled &&
            !this.props.nodeOptions.no_quick_create &&
            request.length > 0 &&
            !raw_result.includes(request) &&
            show_create
        ) {
            options.push({
                label: sprintf(_t(`Create "%s"`), request),
                classList: "o_m2o_dropdown_option o_m2o_dropdown_option_create",
                action: async (params) => {
                    try {
                        await this.props.quickCreate(request, params);
                    } catch {
                        const context = this.getCreationContext(request);
                        return this.openMany2X({context});
                    }
                },
            });
        }

        var search_more = false;
        if (!(this.props.nodeOptions.search_more === undefined)) {
            search_more = is_option_set(this.props.nodeOptions.search_more);
        } else if (!(this.ir_options["access_control.search_more"] === undefined)) {
            search_more = is_option_set(this.ir_options["access_control.search_more"]);
        } else {
            search_more =
                !this.props.noSearchMore && this.props.searchLimit < records.length;
        }
        if (search_more) {
            options.push({
                label: _t("Search More..."),
                action: this.onSearchMore.bind(this, request),
                classList: "o_m2o_dropdown_option o_m2o_dropdown_option_search_more",
            });
        }

        const canCreateEdit =
            "createEdit" in this.activeActions
                ? this.activeActions.createEdit
                : this.activeActions.create;
        if (
            !request.length &&
            !this.props.value &&
            (this.props.quickCreate || canCreateEdit)
        ) {
            options.push({
                label: _t("Start typing..."),
                classList: "o_m2o_start_typing",
                unselectable: true,
            });
        }

        var create_edit = is_option_set(this.props.nodeOptions.create_edit),
            create_edit_undef = this.props.nodeOptions.create_edit === undefined,
            access_control_create_edit_undef =
                this.ir_options["access_control.create_edit"] === undefined,
            access_control_create_edit = is_option_set(
                this.ir_options["access_control.create_edit"]
            );
        var show_create_edit =
            (!this.props.nodeOptions && (access_control_create_edit_undef || access_control_create_edit)) ||
            (this.props.nodeOptions &&
                (create_edit ||
                    (create_edit_undef && (access_control_create_edit_undef || access_control_create_edit))));
        if (show_create_edit && request.length && canCreateEdit) {
            const context = this.getCreationContext(request);
            options.push({
                label: _t("Create and edit..."),
                classList: "o_m2o_dropdown_option o_m2o_dropdown_option_create_edit",
                action: () => this.openMany2X({context}),
            });
        }

        if (!records.length && !this.activeActions.create) {
            options.push({
                label: _t("No records"),
                classList: "o_m2o_no_result",
                unselectable: true,
            });
        }

        return options;
    },
});

Many2XAutocomplete.defaultProps = {
    ...Many2XAutocomplete.defaultProps,
    nodeOptions: {},
};
