/** @odoo-module **/

import { onMounted } from "@odoo/owl";
import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";

// Patch the form view to apply horizontal layout after rendering
patch(FormController.prototype, {
    setup() {
        super.setup();
        onMounted(() => {
            this.applyMedicalFilesHorizontalLayout();
        });
    },

    applyMedicalFilesHorizontalLayout() {
        // Only apply to imaging forms
        if (this.props.resModel !== 'oeh.medical.imaging') {
            return;
        }


        // Wait for DOM to be ready
        setTimeout(() => {
            const container = document.querySelector('.medical_files_container');
            if (!container) {
                setTimeout(() => this.applyMedicalFilesHorizontalLayout(), 1000);
                return;
            }

            this.makeFilesHorizontal(container);

            // Monitor for changes
            const observer = new MutationObserver(() => {
                this.makeFilesHorizontal(container);
            });

            observer.observe(container, {
                childList: true,
                subtree: true
            });

        }, 500);
    },

    makeFilesHorizontal(container) {

        // Find all file-related elements
        const fileElements = container.querySelectorAll(
            '.o_field_many2many_tags .badge, ' +
            '.o_attachment, ' +
            '.o_field_widget > div, ' +
            '.o_field_widget > span'
        );


        fileElements.forEach((element, index) => {
            if (element && !element.querySelector('input') && !element.querySelector('button')) {
                
                // Get filename to calculate dynamic width
                const filename = element.textContent || element.innerText || '';
                const cleanFilename = filename.replace(/\s+/g, ' ').trim();
                
                // Calculate dynamic width based on filename length
                const baseWidth = 120;
                const charWidth = 8; // approximate pixels per character
                const calculatedWidth = Math.max(baseWidth, Math.min(300, cleanFilename.length * charWidth + 40));
                
                
                // Apply minimal horizontal styling without frames
                element.style.cssText = `
                    display: inline-block !important;
                    width: ${calculatedWidth}px !important;
                    min-width: ${baseWidth}px !important;
                    max-width: 300px !important;
                    padding: 8px !important;
                    margin: 4px 8px 4px 0 !important;
                    text-align: center !important;
                    vertical-align: top !important;
                    white-space: normal !important;
                    word-wrap: break-word !important;
                    font-size: 12px !important;
                    line-height: 1.3 !important;
                    color: #495057 !important;
                    background: transparent !important;
                    border: none !important;
                    border-radius: 0 !important;
                    transition: all 0.2s ease !important;
                `;

                // Simplified hover effects without frames
                element.addEventListener('mouseenter', () => {
                    element.style.background = '#f0f8ff';
                    element.style.transform = 'scale(1.02)';
                });

                element.addEventListener('mouseleave', () => {
                    element.style.background = 'transparent';
                    element.style.transform = 'scale(1)';
                });

                // Style images/icons within (keep them compact)
                const img = element.querySelector('img');
                if (img) {
                    img.style.cssText = `
                        max-width: 32px !important;
                        max-height: 32px !important;
                        object-fit: contain !important;
                        margin-right: 8px !important;
                        margin-bottom: 0 !important;
                        vertical-align: middle !important;
                    `;
                }

                // Also handle FA icons
                const icon = element.querySelector('i[class*="fa-"]');
                if (icon) {
                    icon.style.cssText = `
                        font-size: 24px !important;
                        margin-right: 8px !important;
                        vertical-align: middle !important;
                    `;
                }
            }
        });

        // Style the containers for simple horizontal flow
        const tagsContainer = container.querySelector('.o_field_many2many_tags');
        if (tagsContainer) {
            tagsContainer.style.cssText = `
                display: block !important;
                white-space: nowrap !important;
                overflow-x: auto !important;
                padding: 4px 0 !important;
            `;
        }

        const fieldWidget = container.querySelector('.o_field_widget');
        if (fieldWidget) {
            fieldWidget.style.cssText = `
                display: block !important;
                white-space: nowrap !important;
                overflow-x: auto !important;
                padding: 4px 0 !important;
            `;
        }

    }
});