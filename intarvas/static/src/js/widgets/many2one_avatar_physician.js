/** @odoo-module **/

import { Many2OneField, many2OneField } from "@web/views/fields/many2one/many2one_field";
import { registry } from "@web/core/registry";

export class Many2OneAvatarPhysician extends Many2OneField {
    static template = "intarvas.Many2OneAvatarPhysician";

    get avatarUrl() {
        const resId = this.props.record.data[this.props.name]?.[0];
        if (resId) {
            return `/web/image/oeh.medical.physician/${resId}/image_128?unique=${resId}`;
        }
        return "/web/static/img/placeholder.png";
    }

    onExternalButtonClick(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        const resId = this.props.record.data[this.props.name]?.[0];
        if (resId && !this.props.readonly) {
            this.env.services.action.doAction({
                type: 'ir.actions.act_window',
                res_model: 'oeh.medical.physician',
                res_id: resId,
                views: [[false, 'form']],
                target: 'current',
            });
        }
    }
}

export const many2OneAvatarPhysician = {
    ...many2OneField,
    component: Many2OneAvatarPhysician,
    additionalClasses: ["o_field_many2one_avatar"],
};

registry.category("fields").add("many2one_avatar_physician", many2OneAvatarPhysician);