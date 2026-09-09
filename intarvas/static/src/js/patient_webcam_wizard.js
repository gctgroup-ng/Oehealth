/** @odoo-module **/

import { Component, onMounted, onWillUnmount, useRef } from "@odoo/owl";
import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";

patch(FormController.prototype, {
    setup() {
        super.setup();
        
        // Instance-specific webcam state (no global variables)
        this.webcamState = {
            stream: null,
            video: null,
            canvas: null,
            captureBtn: null,
            startCameraBtn: null,
            stopCameraBtn: null,
            retakeBtn: null,
            savePhotoBtn: null,
            noPhotoMsg: null,
            eventListeners: [],
            initialized: false
        };
        
        onMounted(() => {
            if (this.props.resModel === 'oeh.patient.webcam.wizard') {
                this.initWebcamWizard();
            } else {
                // Also check if we're in the webcam wizard by looking for specific elements
                setTimeout(() => {
                    const webcamVideo = document.getElementById('webcam_video');
                    if (webcamVideo) {
                        this.initWebcamWizard();
                    }
                }, 100);
            }
        });
        
        onWillUnmount(() => {
            this.cleanupWebcam();
        });
    },

    initWebcamWizard() {
        // Prevent double initialization
        if (this.webcamState.initialized) {
            return;
        }
        
        // Clean up any existing state first
        this.cleanupWebcam();
        
        // Initialize DOM elements using instance state
        this.webcamState.video = document.getElementById('webcam_video');
        this.webcamState.canvas = document.getElementById('captured_canvas');
        this.webcamState.captureBtn = document.getElementById('capture_btn');
        this.webcamState.startCameraBtn = document.getElementById('start_camera_btn');
        this.webcamState.stopCameraBtn = document.getElementById('stop_camera_btn');
        this.webcamState.retakeBtn = document.getElementById('retake_btn');
        this.webcamState.savePhotoBtn = document.getElementById('save_photo_btn');
        this.webcamState.noPhotoMsg = document.getElementById('no_photo_msg');

        if (!this.webcamState.video || !this.webcamState.canvas) {
            return; // Not the webcam wizard
        }

        // Add event listeners with proper cleanup tracking
        this.addEventListenerSafe(this.webcamState.captureBtn, 'click', this.capturePhoto.bind(this));
        this.addEventListenerSafe(this.webcamState.startCameraBtn, 'click', this.startWebcam.bind(this));
        this.addEventListenerSafe(this.webcamState.stopCameraBtn, 'click', this.stopWebcam.bind(this));
        this.addEventListenerSafe(this.webcamState.retakeBtn, 'click', this.retakePhoto.bind(this));

        this.webcamState.initialized = true;

        // Auto-start camera
        this.startWebcam();
    },

    addEventListenerSafe(element, event, handler) {
        if (element && handler) {
            // Remove any existing listeners first
            const existingIndex = this.webcamState.eventListeners.findIndex(
                listener => listener.element === element && listener.event === event
            );
            if (existingIndex >= 0) {
                const existing = this.webcamState.eventListeners[existingIndex];
                element.removeEventListener(event, existing.handler);
                this.webcamState.eventListeners.splice(existingIndex, 1);
            }
            
            // Add new listener
            element.addEventListener(event, handler);
            this.webcamState.eventListeners.push({ element, event, handler });
        }
    },

    cleanupWebcam() {
        // Stop webcam stream
        if (this.webcamState.stream) {
            this.webcamState.stream.getTracks().forEach(track => {
                track.stop();
            });
            this.webcamState.stream = null;
        }
        
        // Remove all event listeners
        this.webcamState.eventListeners.forEach(({ element, event, handler }) => {
            if (element && handler) {
                element.removeEventListener(event, handler);
            }
        });
        this.webcamState.eventListeners = [];
        
        // Clear video source
        if (this.webcamState.video) {
            this.webcamState.video.srcObject = null;
        }
        
        // Reset state
        this.webcamState.initialized = false;
    },

    async startWebcam() {
        // Stop existing stream first
        if (this.webcamState.stream) {
            this.stopWebcam();
        }
        
        try {
            // Check if navigator.mediaDevices is available
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('getUserMedia is not supported in this browser');
            }

            this.webcamState.stream = await navigator.mediaDevices.getUserMedia({ 
                video: { 
                    width: 320, 
                    height: 240 
                } 
            });
            
            if (this.webcamState.video) {
                this.webcamState.video.srcObject = this.webcamState.stream;
                await this.webcamState.video.play();
                
                // Update button states
                if (this.webcamState.startCameraBtn) this.webcamState.startCameraBtn.style.display = 'none';
                if (this.webcamState.stopCameraBtn) this.webcamState.stopCameraBtn.style.display = 'inline-block';
                if (this.webcamState.captureBtn) this.webcamState.captureBtn.disabled = false;
            }
            
        } catch (err) {
            console.error('Error accessing webcam:', err);
            this.showError(`Unable to access webcam: ${err.message}. Please check permissions and ensure you're using HTTPS.`);
        }
    },

    stopWebcam() {
        if (this.webcamState.stream) {
            this.webcamState.stream.getTracks().forEach(track => {
                track.stop();
            });
            this.webcamState.stream = null;
            
            if (this.webcamState.video) {
                this.webcamState.video.srcObject = null;
            }
            
            // Update button states
            if (this.webcamState.startCameraBtn) this.webcamState.startCameraBtn.style.display = 'inline-block';
            if (this.webcamState.stopCameraBtn) this.webcamState.stopCameraBtn.style.display = 'none';
            if (this.webcamState.captureBtn) this.webcamState.captureBtn.disabled = true;
        }
    },

    capturePhoto() {
        if (!this.webcamState.video || !this.webcamState.canvas) {
            return;
        }
        
        const context = this.webcamState.canvas.getContext('2d');
        context.drawImage(this.webcamState.video, 0, 0, 320, 240);
        
        // Hide "no photo" message and show captured photo
        if (this.webcamState.noPhotoMsg) this.webcamState.noPhotoMsg.style.display = 'none';
        this.webcamState.canvas.style.display = 'block';
        
        // Show retake button and enable save button
        if (this.webcamState.retakeBtn) this.webcamState.retakeBtn.style.display = 'inline-block';
        if (this.webcamState.savePhotoBtn) this.webcamState.savePhotoBtn.disabled = false;
        
        // Convert canvas to base64 and store in hidden field
        const dataURL = this.webcamState.canvas.toDataURL('image/jpeg', 0.8);
        const base64Data = dataURL.split(',')[1]; // Remove data:image/jpeg;base64, prefix
        
        // Store the captured image using RPC call
        this.storeImageData(base64Data);
    },

    retakePhoto() {
        console.log('Retaking photo...');
        if (!this.webcamState.canvas || !this.webcamState.noPhotoMsg) {
            console.error('Canvas or no photo message not available for retake');
            return;
        }
        
        // Clear canvas
        const context = this.webcamState.canvas.getContext('2d');
        context.clearRect(0, 0, 320, 240);
        
        // Show "no photo" message and hide canvas
        this.webcamState.noPhotoMsg.style.display = 'block';
        this.webcamState.canvas.style.display = 'none';
        
        // Hide retake button and disable save button
        if (this.webcamState.retakeBtn) this.webcamState.retakeBtn.style.display = 'none';
        if (this.webcamState.savePhotoBtn) this.webcamState.savePhotoBtn.disabled = true;
        
        console.log('Photo retake completed, clearing stored image data...');
        
        // Clear the captured image
        this.storeImageData(false);
    },


    async storeImageData(imageData) {
        console.log('Storing image data using foolproof method...');
        console.log('Image data length:', imageData ? imageData.length : 0);
        
        try {
            // Get patient ID from URL
            const patientId = this.extractPatientIdFromUrl();
            console.log('Patient ID for storage:', patientId);
            
            if (!patientId) {
                console.error('No patient ID found in URL!');
                this.showError('Unable to identify patient. Please try again.');
                return;
            }
            
            if (!imageData) {
                console.error('No image data to store!');
                this.showError('No image data captured. Please try again.');
                return;
            }
            
            // Call the foolproof server method to create wizard and store image
            console.log('Calling server to create wizard and store image...');
            const result = await rpc("/web/dataset/call_kw/oeh.patient.webcam.wizard/create_wizard_and_store_image", {
                model: "oeh.patient.webcam.wizard",
                method: "create_wizard_and_store_image",
                args: [patientId, imageData],
                kwargs: {}
            });
            
            console.log('Server response:', result);
            
            if (result && result.success) {
                console.log(`✅ SUCCESS: Created wizard ${result.wizard_id} with image (${result.image_length} bytes)!`);
            } else {
                console.error('❌ Server failed to store image:', result.error || 'Unknown error');
                this.showError('Failed to store image on server: ' + (result.error || 'Unknown error'));
            }
            
        } catch (error) {
            console.error('❌ RPC call failed:', error);
            this.showError('Failed to store captured image: ' + error.message);
        }
    },

    getWizardId() {
        console.log('Attempting to get wizard ID...');
        console.log('Current URL:', window.location.href);
        console.log('Props available:', !!this.props);
        
        // Debug: Log all props
        if (this.props) {
            console.log('Full props object:', this.props);
            console.log('Props keys:', Object.keys(this.props));
            console.log('resId:', this.props.resId);
            console.log('resIds:', this.props.resIds);
            console.log('resModel:', this.props.resModel);
        }
        
        // Method 1: Try to get from props (most reliable for Odoo 18)
        if (this.props && this.props.resId) {
            console.log('Found wizard ID from props:', this.props.resId);
            return this.props.resId;
        }
        
        // Method 1b: Try to get from props.resIds (sometimes it's an array)
        if (this.props && this.props.resIds && this.props.resIds.length > 0) {
            console.log('Found wizard ID from props.resIds:', this.props.resIds[0]);
            return this.props.resIds[0];
        }

        // Method 2: Look for the most recent ID in the URL hash (Odoo 18 format)
        const hash = window.location.hash;
        console.log('URL hash:', hash);
        
        // Try to find id in hash like: #id=44&model=oeh.patient.webcam.wizard
        const hashIdMatch = hash.match(/[#&]id=(\d+)/);
        if (hashIdMatch) {
            console.log('Found wizard ID from hash id param:', hashIdMatch[1]);
            return parseInt(hashIdMatch[1]);
        }
        
        // Try to find any ID in the hash path
        const hashPathMatch = hash.match(/\/(\d+)(?:\/|$|\?|&)/);
        if (hashPathMatch) {
            console.log('Found wizard ID from hash path:', hashPathMatch[1]);
            return parseInt(hashPathMatch[1]);
        }

        // Method 3: Try to extract from the URL path (like /odoo/action-547/22)
        const pathMatch = window.location.pathname.match(/\/(\d+)(?:\/|$)/);
        if (pathMatch) {
            const pathId = parseInt(pathMatch[1]);
            console.log('Found potential wizard ID from path:', pathId);
            // Verify this looks like a reasonable wizard ID (not too small like action numbers)
            if (pathId > 10) { // Assume wizard IDs are > 10 to avoid action numbers
                return pathId;
            }
        }

        // Method 4: Try URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const id = urlParams.get('id');
        if (id) {
            console.log('Found wizard ID from URL params:', id);
            return parseInt(id);
        }

        // Method 5: Try form element data attributes (check for wizard-specific ones)
        const formElement = document.querySelector('.o_form_view[data-res-model="oeh.patient.webcam.wizard"]');
        if (formElement) {
            const resId = formElement.getAttribute('data-res-id') || 
                         formElement.getAttribute('data-record-id') ||
                         formElement.getAttribute('data-id');
            if (resId) {
                console.log('Found wizard ID from wizard form element:', resId);
                return parseInt(resId);
            }
        }

        // Method 6: Check any form element as fallback
        const anyFormElement = document.querySelector('.o_form_view');
        if (anyFormElement) {
            console.log('Form element attributes:', {
                'data-res-model': anyFormElement.getAttribute('data-res-model'),
                'data-res-id': anyFormElement.getAttribute('data-res-id'),
                'data-record-id': anyFormElement.getAttribute('data-record-id'),
                'data-id': anyFormElement.getAttribute('data-id')
            });
            
            const resId = anyFormElement.getAttribute('data-res-id') || 
                         anyFormElement.getAttribute('data-record-id') ||
                         anyFormElement.getAttribute('data-id');
            if (resId) {
                console.log('Found wizard ID from any form element:', resId);
                return parseInt(resId);
            }
        }

        console.error('No wizard ID found using any method!');
        console.log('Available form elements:', document.querySelectorAll('.o_form_view').length);
        
        return null;
    },

    async getCurrentWizardId() {
        console.log('Getting current wizard ID from server...');
        
        // First try the old method
        const staticWizardId = this.getWizardId();
        if (staticWizardId) {
            console.log('Found wizard ID from client methods:', staticWizardId);
            return staticWizardId;
        }
        
        // If that fails, get it from server by finding the most recent wizard for this patient
        try {
            // Extract patient ID from URL
            const patientId = this.extractPatientIdFromUrl();
            console.log('Extracted patient ID from URL:', patientId);
            
            if (patientId) {
                // Get the most recent wizard for this patient
                const result = await rpc("/web/dataset/search_read", {
                    model: "oeh.patient.webcam.wizard",
                    domain: [["patient_id", "=", patientId]],
                    fields: ["id", "patient_id"],
                    sort: "id desc",
                    limit: 1
                });
                
                console.log('Server wizard search result:', result);
                
                if (result && result.length > 0) {
                    const wizardId = result[0].id;
                    console.log('Found current wizard ID from server:', wizardId);
                    return wizardId;
                }
            }
        } catch (error) {
            console.error('Failed to get wizard ID from server:', error);
        }
        
        console.error('Unable to determine current wizard ID');
        return null;
    },

    getCurrentWizardRecord() {
        // Try to get the current wizard record ID from props or context
        if (this.props && this.props.resId) {
            return this.props.resId;
        }
        
        // For new records, this might be undefined/false
        // The server method will use 'self' to refer to current wizard
        return null;
    },

    extractPatientIdFromUrl() {
        // Extract patient ID from URL like http://localhost:1818/odoo/action-547/22
        const pathMatch = window.location.pathname.match(/\/(\d+)(?:\/|$)/);
        if (pathMatch) {
            return parseInt(pathMatch[1]);
        }
        return null;
    },

    async getPatientId() {
        console.log('Attempting to get patient ID...');
        
        try {
            const wizardId = this.getWizardId();
            if (wizardId) {
                // Get patient ID from wizard record
                const wizardData = await rpc("/web/dataset/call_kw/oeh.patient.webcam.wizard/read", {
                    model: "oeh.patient.webcam.wizard",
                    method: "read",
                    args: [wizardId, ['patient_id']],
                    kwargs: {}
                });
                
                if (wizardData && wizardData.length > 0 && wizardData[0].patient_id) {
                    const patientId = wizardData[0].patient_id[0]; // patient_id is a Many2one field [id, name]
                    console.log('Found patient ID from wizard:', patientId);
                    return patientId;
                }
            }
        } catch (error) {
            console.error('Error getting patient ID:', error);
        }
        
        return null;
    },

    showError(message) {
        // Create and show error notification
        if (this.notification) {
            this.notification.add(message, {
                title: "Webcam Error",
                type: "danger",
            });
        } else {
            alert(message); // Fallback
        }
    }
});