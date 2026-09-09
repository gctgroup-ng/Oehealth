/** @odoo-module **/

import { registry } from "@web/core/registry";
import { TextField } from "@web/views/fields/text/text_field";
import { textField } from "@web/views/fields/text/text_field";
import { markup } from "@odoo/owl";

export class ResultIndicatorField extends TextField {
    static template = "intarvas_lab.ResultIndicatorField";

    get displayValue() {
        // Get the raw field value
        let rawValue = this.props.record.data[this.props.name] || '';
        const normalRange = this.props.record?.data?.normal_range || '';
        const displayType = this.props.record?.data?.display_type;
        
        // Clean HTML wrapper if present (like <p style="margin-bottom: 0px;">24</p>)
        let cleanValue = rawValue;
        if (typeof rawValue === 'string' && rawValue.includes('<p') && rawValue.includes('</p>')) {
            const match = rawValue.match(/<p[^>]*>(.*?)<\/p>/);
            if (match) {
                cleanValue = match[1];
            }
        }
        
        
        // If no value, range, or it's a display type, show as normal
        if (!cleanValue || !normalRange || displayType) {
            return rawValue;
        }

        const indicator = this._getIndicator(cleanValue, normalRange);
        
        if (indicator) {
            // Return text with styled indicator using markup
            return markup(`${cleanValue} <span class="indicator-arrow">${indicator}</span>`);
        }
        return rawValue;
    }

    _getIndicator(result, normalRange) {
        try {
            const resultValue = parseFloat(result.toString().trim());
            if (isNaN(resultValue)) return '';
            
            const range = normalRange.toString().trim();
            
            // Handle range patterns like "10-20"
            if (range.includes('-') && !range.startsWith('<') && !range.startsWith('>')) {
                const rangeParts = range.replace(/\s/g, '').split('-');
                if (rangeParts.length === 2) {
                    const minVal = parseFloat(rangeParts[0]);
                    const maxVal = parseFloat(rangeParts[1]);
                    if (!isNaN(minVal) && !isNaN(maxVal)) {
                        if (resultValue > maxVal) return '↑';
                        if (resultValue < minVal) return '↓';
                    }
                }
            }
            // Handle "< 5" pattern
            else if (range.startsWith('<')) {
                const maxVal = parseFloat(range.replace('<', '').trim());
                if (!isNaN(maxVal) && resultValue > maxVal) return '↑';
            }
            // Handle "> 100" pattern
            else if (range.startsWith('>')) {
                const minVal = parseFloat(range.replace('>', '').trim());
                if (!isNaN(minVal) && resultValue < minVal) return '↓';
            }
        } catch (error) {
            return '';
        }
        return '';
    }
}

export const resultIndicatorField = {
    ...textField,
    component: ResultIndicatorField,
};

registry.category("fields").add("result_indicator", resultIndicatorField);