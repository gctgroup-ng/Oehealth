/** @odoo-module **/

import { CharField, charField } from "@web/views/fields/char/char_field";
import { registry } from "@web/core/registry";

export class NameAvatarPatient extends CharField {
    static template = "intarvas.NameAvatarPatient";

    get avatarUrl() {
        const recordId = this.props.record.resId;
        if (recordId) {
            return `/web/image/oeh.medical.patient/${recordId}/image_128?unique=${recordId}`;
        }
        return "/web/static/img/placeholder.png";
    }
    
    get displayValue() {
        return this.props.record.data[this.props.name] || this.props.value || "";
    }
}

export const nameAvatarPatient = {
    ...charField,
    component: NameAvatarPatient,
    additionalClasses: ["o_field_name_avatar"],
};

registry.category("fields").add("name_avatar_patient", nameAvatarPatient);