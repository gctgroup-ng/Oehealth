/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart, useRef, onMounted } from "@odoo/owl";

export class Many2ManyTagsDisplayField extends Component {
    setup() {
        this.orm = useService("orm");
        this.containerRef = useRef("container");
        
        this.state = useState({
            allOptions: [],
            loading: false,
        });
        
        onWillStart(async () => {
            await this.loadAllOptions();
        });

        onMounted(() => {
            this.setupEventListeners();
        });
    }

    async loadAllOptions() {
        const relation = this.props.relation || 
                        this.props.field?.relation ||
                        this.props.record?.fields?.[this.props.name]?.relation;
        
        if (!relation) return;
        
        this.state.loading = true;
        try {
            const domain = this.props.domain || [];
            const allRecords = await this.orm.searchRead(
                relation,
                domain,
                ["id", "name", "display_name"],
                {}
            );
            this.state.allOptions = allRecords;
        } catch (error) {
            console.error("Error loading options:", error);
        } finally {
            this.state.loading = false;
        }
    }

    setupEventListeners() {
        const container = this.containerRef.el;
        if (!container) return;

        container.addEventListener('click', (e) => {
            const availableTag = e.target.closest('.o_tag_available');
            if (availableTag) {
                e.preventDefault();
                e.stopPropagation();
                const optionId = parseInt(availableTag.dataset.optionId);
                this.addTag(optionId);
                return;
            }

            const removeButton = e.target.closest('.o_tag_remove');
            if (removeButton) {
                e.preventDefault();
                e.stopPropagation();
                const recordId = parseInt(removeButton.dataset.recordId);
                this.removeTag(recordId);
                return;
            }
        });
    }

    get selectedRecords() {
        const fieldValue = this.props.record?.data?.[this.props.name];
        if (!fieldValue) return [];
        
        // Handle StaticList (Odoo 19 many2many field structure)
        if (fieldValue && typeof fieldValue === 'object') {
            
            // First try to use _currentIds to get all selected IDs
            if (fieldValue._currentIds && Array.isArray(fieldValue._currentIds) && fieldValue._currentIds.length > 0) {
                // Convert _currentIds to records by looking them up in allOptions
                return fieldValue._currentIds.map(id => {
                    const option = this.state.allOptions.find(opt => opt.id === id);
                    if (option) {
                        return option;
                    }
                    // If not found in allOptions, create a minimal record structure
                    return { id: id, resId: id, data: { id: id, name: `Test ${id}` } };
                });
            }
            
            // Check for records property
            if (fieldValue.records) {
                return Array.from(fieldValue.records || []);
            }
            
            // Check for resIds (many2many IDs)
            if (fieldValue.resIds && Array.isArray(fieldValue.resIds)) {
                // Convert resIds to records by looking them up in allOptions
                return fieldValue.resIds.map(id => {
                    const option = this.state.allOptions.find(opt => opt.id === id);
                    return option || { id: id, resId: id, data: { id: id } };
                });
            }
            
            // Check for data property (sometimes the data is nested)
            if (fieldValue.data && Array.isArray(fieldValue.data)) {
                return fieldValue.data;
            }
        }
        
        // Handle array directly
        if (Array.isArray(fieldValue)) {
            return fieldValue;
        }
        
        return [];
    }

    get selectedIds() {
        const records = this.selectedRecords;
        const ids = records.map(record => {
            // For Proxy(Record) objects from StaticList
            if (record && record.data && record.data.id) {
                return record.data.id;
            }
            // For direct objects
            return record.resId || record.id;
        }).filter(id => id !== undefined);
        return ids;
    }

    get unselectedOptions() {
        const selectedIds = this.selectedIds;
        return this.state.allOptions.filter(option => !selectedIds.includes(option.id));
    }

    async addTag(optionId) {
        if (this.props.readonly) return;
        
        try {
            // Get current selected IDs
            const currentIds = this.selectedIds;
            
            // Don't add if already selected
            if (currentIds.includes(optionId)) return;
            
            // Create commands to set all IDs (current + new one)
            const allIds = [...currentIds, optionId];
            const commands = [[6, false, allIds]]; // Replace with all IDs
            
            // Update using the field's update mechanism
            await this.props.record.update({
                [this.props.name]: commands
            });
            
            // Force the record to be marked as dirty for save
            if (this.props.record.model && this.props.record.model.bus) {
                this.props.record.model.bus.trigger('field_changed', {
                    dataPointID: this.props.record.id,
                    changes: { [this.props.name]: commands }
                });
            }
        } catch (error) {
            console.error("Error adding tag:", error);
        }
    }

    async removeTag(recordId) {
        if (this.props.readonly) return;
        
        try {
            // Get current selected IDs
            const currentIds = this.selectedIds;
            
            // Remove the specified ID
            const allIds = currentIds.filter(id => id !== recordId);
            const commands = [[6, false, allIds]]; // Replace with filtered IDs
            
            
            // Update using the field's update mechanism
            await this.props.record.update({
                [this.props.name]: commands
            });
        } catch (error) {
            console.error("Error removing tag:", error);
        }
    }

    getDisplayName(record) {
        // For available options (from allOptions array)
        if (record && (record.name || record.display_name)) {
            return record.display_name || record.name;
        }
        
        // For Proxy(Record) objects from StaticList
        if (record && record.data) {
            if (record.data.display_name) {
                return record.data.display_name;
            }
            if (record.data.name) {
                return record.data.name;
            }
        }
        
        // For selected records, lookup in allOptions
        const recordId = record?.resId || record?.id || record?.data?.id;
        if (recordId && this.state.allOptions.length > 0) {
            const foundOption = this.state.allOptions.find(option => option.id === recordId);
            if (foundOption) {
                return foundOption.display_name || foundOption.name;
            }
        }
        
        return `Record ${recordId || 'Unknown'}`;
    }
}

Many2ManyTagsDisplayField.template = "intarvas.Many2ManyTagsDisplayField";
Many2ManyTagsDisplayField.supportedTypes = ["many2many"];
Many2ManyTagsDisplayField.props = {
    "*": true,
};

registry.category("fields").add("many2many_tags_display", {
    component: Many2ManyTagsDisplayField,
});