/** @odoo-module **/

import { registry } from "@web/core/registry";
import { TextField } from "@web/views/fields/text/text_field";
import { markup, onWillStart, onPatched } from "@odoo/owl";

export class ResultIndicatorField extends TextField {

    setup() {
        super.setup();
        onWillStart(() => {
            this.computeDisplayValue();
        });
        onPatched(() => {
            this.computeDisplayValue();
        });
    }

    computeDisplayValue() {
        // Override the parent's display logic
        const record = this.props.record;
        const fieldName = this.props.name;
        
        if (!record?.data || !fieldName) {
            return;
        }
        
        const result = record.data[fieldName] || "";
        const normalRange = record.data.normal_range;
        const displayType = record.data.display_type;
        
        // If no result, no range, or it's a display type, show as normal
        if (!result || !normalRange || displayType) {
            return;
        }
        
        const indicator = this.getResultIndicator(result, normalRange);
        if (indicator && this.props.readonly) {
            // Only show indicators in readonly mode
            const element = this.el?.querySelector('.o_field_text');
            if (element) {
                element.innerHTML = `${result} <span style="color: red; font-weight: bold;">${indicator}</span>`;
            }
        }
    }

    getResultIndicator(result, normalRange) {
        try {
            const resultValue = parseFloat(result.toString().trim());
            if (isNaN(resultValue)) return '';
            
            const range = normalRange.toString().trim();
            
            // Parse range patterns like "10-20", "< 5", "> 100", "≤ 10", "≥ 5"
            if (range.includes('-') && !range.startsWith('<') && !range.startsWith('>')) {
                // Range format: "10-20" or "10 - 20"
                const rangeParts = range.replace(/\s/g, '').split('-');
                if (rangeParts.length === 2) {
                    const minVal = parseFloat(rangeParts[0]);
                    const maxVal = parseFloat(rangeParts[1]);
                    if (!isNaN(minVal) && !isNaN(maxVal)) {
                        if (minVal <= resultValue && resultValue <= maxVal) {
                            return '';  // Normal, no indicator
                        } else if (resultValue > maxVal) {
                            return '↑';  // High
                        } else {
                            return '↓';  // Low
                        }
                    }
                }
            } else if (range.startsWith('<') || range.startsWith('≤')) {
                // Less than format: "< 5" or "≤ 5"
                const maxVal = parseFloat(range.replace(/[<≤]/g, '').trim());
                if (!isNaN(maxVal) && resultValue > maxVal) {
                    return '↑';
                }
                return '';
            } else if (range.startsWith('>') || range.startsWith('≥')) {
                // Greater than format: "> 100" or "≥ 100"
                const minVal = parseFloat(range.replace(/[>≥]/g, '').trim());
                if (!isNaN(minVal) && resultValue < minVal) {
                    return '↓';
                }
                return '';
            } else {
                // Try to parse as single value with tolerance
                const normalVal = parseFloat(range);
                if (!isNaN(normalVal)) {
                    // Consider ±10% as normal range for single values
                    const tolerance = normalVal * 0.1;
                    if (Math.abs(resultValue - normalVal) <= tolerance) {
                        return '';
                    } else if (resultValue > normalVal) {
                        return '↑';
                    } else {
                        return '↓';
                    }
                }
            }
        } catch (error) {
            return '';
        }
        return '';
    }
}

registry.category("fields").add("result_indicator", ResultIndicatorField);