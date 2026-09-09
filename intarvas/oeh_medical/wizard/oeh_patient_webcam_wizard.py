##############################################################################
#    Copyright (C) 2015 - Present, intarvas (<https://www.intarvas.in>). All Rights Reserved
#    intarvas, Hospital Management Solutions

# Odoo Proprietary License v1.0
#
# This software and associated files (the "Software") may only be used (executed,
# modified, executed after modifications) if you have purchased a valid license
# from the authors, typically via Odoo Apps, intarvas.in, intarvas.com, or if you have received a written
# agreement from the authors of the Software.
#
# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without copying
# any source code or material from the Software. You may distribute those
# modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the Software
# or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

##############################################################################

import base64
from odoo import fields, models, api, _
from odoo.exceptions import UserError


class intarvasPatientWebcamWizard(models.TransientModel):
    _name = "oeh.patient.webcam.wizard"
    _description = "Patient Webcam Photo Capture Wizard"

    patient_id = fields.Many2one('oeh.medical.patient', string='Patient', required=True)
    patient_name = fields.Char(related='patient_id.name', readonly=True)
    captured_image = fields.Binary(string='Captured Photo')
    captured_image_filename = fields.Char(string='Filename', default='patient_photo.jpg')

    def save_photo(self):
        """Save the captured photo to patient profile"""
        import logging
        _logger = logging.getLogger(__name__)
        
        _logger.info(f"SAVE_PHOTO: Starting save process for wizard {self.id}")
        
        # Refresh the record to get latest data
        self = self.sudo().browse(self.id)
        _logger.info(f"SAVE_PHOTO: Wizard refreshed, patient: {self.patient_id.name if self.patient_id else 'None'}")
        _logger.info(f"SAVE_PHOTO: Current wizard captured_image length: {len(self.captured_image) if self.captured_image else 0}")
        
        # Check if there's a pending webcam image stored during the session
        _logger.info("SAVE_PHOTO: Checking for pending webcam capture...")
        
        # First check current wizard
        if self.captured_image:
            captured_image = self.captured_image
            _logger.info(f"SAVE_PHOTO: Found image in current wizard {self.id}, length: {len(captured_image)}")
        else:
            # Search for recent wizards with images for this patient
            _logger.info("SAVE_PHOTO: Searching for most recent wizard with captured image...")
            all_wizards = self.search([
                ('patient_id', '=', self.patient_id.id),
                ('captured_image', '!=', False)
            ], order='id desc', limit=5)  # Get last 5 wizards to debug
            
            _logger.info(f"SAVE_PHOTO: Found {len(all_wizards)} wizards with images: {[w.id for w in all_wizards]}")
            
            if all_wizards:
                # Use the most recent wizard with image data
                source_wizard = all_wizards[0]
                captured_image = source_wizard.captured_image
                _logger.info(f"SAVE_PHOTO: Using image from wizard {source_wizard.id}, length: {len(captured_image)}")
                _logger.info(f"SAVE_PHOTO: Current wizard is {self.id}, source wizard is {source_wizard.id}")
            else:
                # Try the new method to get latest image
                _logger.info("SAVE_PHOTO: Using latest image lookup method...")
                latest_result = self.get_latest_webcam_image_for_patient(self.patient_id.id)
                
                if latest_result['found']:
                    captured_image = latest_result['image_data']
                    _logger.info(f"SAVE_PHOTO: Found latest image from wizard {latest_result['wizard_id']}, length: {latest_result['image_length']}")
                else:
                    captured_image = False
                    _logger.warning(f"SAVE_PHOTO: No captured image found in any wizard for patient {self.patient_id.id}!")
                    
                    # Debug: Search ALL wizards regardless of patient
                    debug_wizards = self.search([('captured_image', '!=', False)], order='id desc', limit=3)
                    _logger.info(f"SAVE_PHOTO: DEBUG - Recent wizards with ANY images: {[(w.id, w.patient_id.id, len(w.captured_image)) for w in debug_wizards]}")
        
        # Update the patient's image
        if captured_image:
            try:
                _logger.info(f"SAVE_PHOTO: Updating patient {self.patient_id.id} image...")
                result = self.patient_id.write({
                    'image_1920': captured_image
                })
                _logger.info(f"SAVE_PHOTO: Patient image update result: {result}")
                
                # Verify the update
                self.patient_id.invalidate_recordset(['image_1920'])
                final_length = len(self.patient_id.image_1920) if self.patient_id.image_1920 else 0
                _logger.info(f"SAVE_PHOTO: Final patient image length: {final_length}")
                
                if final_length > 0:
                    _logger.info("✅ SAVE_PHOTO: Patient image saved successfully!")
                else:
                    _logger.error("❌ SAVE_PHOTO: Patient image save failed - no data after write!")
                    
            except Exception as save_error:
                _logger.error(f"SAVE_PHOTO: Exception during patient image update: {str(save_error)}")
                import traceback
                _logger.error(f"SAVE_PHOTO: Traceback: {traceback.format_exc()}")
        else:
            _logger.error("SAVE_PHOTO: No captured image to save!")
        
        # Log activity
        try:
            self.patient_id.message_post(
                body=_('Patient photo updated via webcam capture.'),
                message_type='notification'
            )
            _logger.info("SAVE_PHOTO: Activity logged successfully")
        except Exception as msg_error:
            _logger.error(f"SAVE_PHOTO: Failed to log activity: {str(msg_error)}")
        
        _logger.info("SAVE_PHOTO: Process completed, closing wizard")
        return {'type': 'ir.actions.act_window_close'}

    def capture_photo(self):
        """Handle photo capture from JavaScript"""
        # This method will be called from JavaScript to store the captured image
        return True
    
    @api.model
    def store_captured_image(self, wizard_id, image_data):
        """Store captured image data from JavaScript"""
        import logging
        _logger = logging.getLogger(__name__)
        
        _logger.info(f"Storing captured image - Wizard ID: {wizard_id}, Image data length: {len(image_data) if image_data else 0}")
        
        # Validate and fix image data format
        if image_data:
            try:
                # Check if it's valid base64
                import base64
                decoded = base64.b64decode(image_data)
                _logger.info(f"Image data validation: valid base64, decoded size: {len(decoded)} bytes")
                
                # Check if it starts with valid image signature
                if decoded.startswith(b'\xff\xd8\xff'):  # JPEG signature
                    _logger.info("Image format: JPEG - valid")
                elif decoded.startswith(b'\x89PNG'):  # PNG signature
                    _logger.info("Image format: PNG - valid")
                else:
                    _logger.warning(f"Image format: Unknown - first bytes: {decoded[:10]}")
                    
            except Exception as validation_error:
                _logger.error(f"Image data validation failed: {str(validation_error)}")
                return False
        
        try:
            # Use sudo() to ensure we can access the wizard record
            wizard = self.sudo().browse(wizard_id)
            
            if not wizard.exists():
                _logger.error(f"Wizard with ID {wizard_id} does not exist")
                
                # Try to find any active wizard for debugging
                active_wizards = self.sudo().search([])
                _logger.info(f"Active wizards found: {[w.id for w in active_wizards]}")
                
                # Alternative approach: Try to find the most recent wizard for any patient
                if active_wizards:
                    latest_wizard = active_wizards[-1]  # Get the most recent one
                    _logger.info(f"Using latest available wizard: {latest_wizard.id}")
                    wizard = latest_wizard
                else:
                    _logger.error("No active wizards found at all!")
                    return False
            
            if wizard and image_data:
                # Use sudo() for the write operation as well
                _logger.info(f"Writing image data to wizard {wizard.id}, data length: {len(image_data)}")
                
                try:
                    result = wizard.sudo().write({'captured_image': image_data})
                    _logger.info(f"Wizard write operation result: {result}")
                    
                    # Immediately verify the write operation
                    wizard.invalidate_recordset(['captured_image'])
                    wizard_after_write = self.sudo().browse(wizard.id)
                    stored_length = len(wizard_after_write.captured_image) if wizard_after_write.captured_image else 0
                    _logger.info(f"VERIFICATION: Wizard {wizard.id} captured_image length after write: {stored_length}")
                    
                    if stored_length > 0:
                        _logger.info(f"✅ SUCCESS: Image successfully stored in wizard {wizard.id}")
                        return True
                    else:
                        _logger.error(f"❌ FAILED: Image not found in wizard {wizard.id} after write operation!")
                        return False
                        
                except Exception as write_error:
                    _logger.error(f"Exception during wizard write: {str(write_error)}")
                    import traceback
                    _logger.error(f"Write traceback: {traceback.format_exc()}")
                    return False
            else:
                _logger.warning(f"No image data provided for wizard {wizard_id}")
                return False
                
        except Exception as e:
            _logger.error(f"Error storing image for wizard {wizard_id}: {str(e)}")
            import traceback
            _logger.error(f"Full traceback: {traceback.format_exc()}")
            return False
    
    @api.model 
    def store_image_by_patient(self, patient_id, image_data):
        """Alternative method to store image directly by patient ID"""
        import logging
        _logger = logging.getLogger(__name__)
        
        try:
            # Find or create a wizard for this patient
            wizard = self.sudo().search([('patient_id', '=', patient_id)], limit=1)
            
            if not wizard:
                # Create a new wizard if none exists
                wizard = self.sudo().create({
                    'patient_id': patient_id,
                    'captured_image': image_data
                })
                _logger.info(f"Created new wizard {wizard.id} for patient {patient_id}")
            else:
                # Update existing wizard
                wizard.write({'captured_image': image_data})
                _logger.info(f"Updated existing wizard {wizard.id} for patient {patient_id}")
            
            # IMMEDIATELY UPDATE THE PATIENT RECORD
            if image_data:
                try:
                    patient = self.env['oeh.medical.patient'].sudo().browse(patient_id)
                    if patient.exists():
                        _logger.info(f"ALTERNATIVE METHOD: Attempting to update patient {patient_id} with image data length: {len(image_data)}")
                        _logger.info(f"ALTERNATIVE METHOD: Patient name: {patient.name}")
                        
                        result = patient.write({
                            'image_1920': image_data
                        })
                        _logger.info(f"ALTERNATIVE METHOD: Patient {patient_id} image update result: {result}")
                        
                        # Verify the update
                        patient.invalidate_recordset(['image_1920'])
                        updated_image_length = len(patient.image_1920) if patient.image_1920 else 0
                        _logger.info(f"ALTERNATIVE METHOD VERIFICATION: Patient {patient_id} image_1920 length after update: {updated_image_length}")
                        
                        # Log activity
                        patient.message_post(
                            body=_('Patient photo updated via webcam capture.'),
                            message_type='notification'
                        )
                        
                except Exception as patient_update_error:
                    _logger.error(f"ALTERNATIVE METHOD EXCEPTION: {str(patient_update_error)}")
                    import traceback
                    _logger.error(f"ALTERNATIVE METHOD traceback: {traceback.format_exc()}")
            
            return wizard.id
            
        except Exception as e:
            _logger.error(f"Error storing image for patient {patient_id}: {str(e)}")
            return False
    
    @api.model
    def create_wizard_and_store_image(self, patient_id, image_data):
        """Create a new wizard and store image data - foolproof method"""
        import logging
        _logger = logging.getLogger(__name__)
        
        try:
            _logger.info(f"CREATE_AND_STORE: Creating new wizard for patient {patient_id}")
            _logger.info(f"CREATE_AND_STORE: Image data length: {len(image_data) if image_data else 0}")
            
            # Create a new wizard with the image data
            wizard = self.create({
                'patient_id': patient_id,
                'captured_image': image_data
            })
            
            _logger.info(f"CREATE_AND_STORE: ✅ Created wizard {wizard.id} with image")
            
            # Verify the creation
            wizard.invalidate_recordset(['captured_image'])
            stored_length = len(wizard.captured_image) if wizard.captured_image else 0
            _logger.info(f"CREATE_AND_STORE: Verification - wizard {wizard.id} image length: {stored_length}")
            
            return {
                'success': True,
                'wizard_id': wizard.id,
                'image_length': stored_length
            }
            
        except Exception as e:
            _logger.error(f"CREATE_AND_STORE: Failed to create wizard: {str(e)}")
            import traceback
            _logger.error(f"CREATE_AND_STORE: Traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': str(e)
            }

    @api.model
    def refresh_patient_image(self, patient_id):
        """Force refresh patient image data for frontend"""
        import logging
        _logger = logging.getLogger(__name__)
        
        try:
            patient = self.env['oeh.medical.patient'].sudo().browse(patient_id)
            if patient.exists():
                # Force cache invalidation
                patient.invalidate_recordset(['image_1920'])
                
                # Return current image data
                image_data = {
                    'patient_id': patient_id,
                    'patient_name': patient.name,
                    'image_1920': patient.image_1920,
                    'has_image': bool(patient.image_1920),
                    'image_length': len(patient.image_1920) if patient.image_1920 else 0,
                    'timestamp': str(patient.write_date)
                }
                _logger.info(f"Refreshed patient {patient_id} image data: has_image={image_data['has_image']}, length={image_data['image_length']}")
                return image_data
            else:
                _logger.error(f"Patient {patient_id} not found for refresh")
                return False
                
        except Exception as e:
            _logger.error(f"Error refreshing patient {patient_id} image: {str(e)}")
            return False

    @api.model
    def test_image_display(self, image_data):
        """Test if image data can be properly displayed"""
        import logging
        _logger = logging.getLogger(__name__)
        
        try:
            if not image_data:
                return {'valid': False, 'error': 'No image data provided'}
                
            # Validate base64
            import base64
            try:
                decoded = base64.b64decode(image_data)
                _logger.info(f"Test image: Base64 valid, decoded size: {len(decoded)}")
            except Exception as b64_error:
                return {'valid': False, 'error': f'Invalid base64: {str(b64_error)}'}
            
            # Check image format
            if decoded.startswith(b'\xff\xd8\xff'):
                format_type = 'JPEG'
            elif decoded.startswith(b'\x89PNG'):
                format_type = 'PNG'
            else:
                format_type = 'Unknown'
                
            # Try to process with Odoo's image tools
            try:
                from odoo.tools import image
                processed = image.image_process(image_data, size=(300, 300))
                process_success = bool(processed)
                _logger.info(f"Test image: Odoo processing {'successful' if process_success else 'failed'}")
            except Exception as process_error:
                process_success = False
                _logger.warning(f"Test image: Odoo processing failed: {str(process_error)}")
            
            result = {
                'valid': True,
                'format': format_type,
                'size': len(decoded),
                'odoo_processable': process_success,
                'base64_length': len(image_data)
            }
            
            _logger.info(f"Test image result: {result}")
            return result
            
        except Exception as e:
            _logger.error(f"Error testing image: {str(e)}")
            return {'valid': False, 'error': str(e)}
    
    def store_image_in_current_wizard(self, image_data):
        """Store image in the current wizard instance"""
        import logging
        _logger = logging.getLogger(__name__)
        
        _logger.info(f"DIRECT STORE: Storing image in current wizard {self.id}")
        _logger.info(f"DIRECT STORE: Patient: {self.patient_id.name if self.patient_id else 'None'}")
        _logger.info(f"DIRECT STORE: Image data length: {len(image_data) if image_data else 0}")
        
        if image_data:
            try:
                self.write({'captured_image': image_data})
                _logger.info(f"DIRECT STORE: ✅ Image stored successfully in wizard {self.id}")
                return True
            except Exception as e:
                _logger.error(f"DIRECT STORE: ❌ Failed to store image: {str(e)}")
                return False
        else:
            _logger.warning("DIRECT STORE: No image data provided")
            return False
    
    @api.model
    def get_latest_webcam_image_for_patient(self, patient_id):
        """Get the most recent webcam image for a patient"""
        import logging
        _logger = logging.getLogger(__name__)
        
        _logger.info(f"GET_LATEST: Searching for latest webcam image for patient {patient_id}")
        
        # Search for the most recent wizard with captured image for this patient
        wizards = self.search([
            ('patient_id', '=', patient_id),
            ('captured_image', '!=', False)
        ], order='id desc', limit=1)
        
        if wizards:
            wizard = wizards[0]
            _logger.info(f"GET_LATEST: Found image in wizard {wizard.id}, length: {len(wizard.captured_image)}")
            return {
                'found': True,
                'wizard_id': wizard.id,
                'image_data': wizard.captured_image,
                'image_length': len(wizard.captured_image)
            }
        else:
            _logger.warning(f"GET_LATEST: No webcam image found for patient {patient_id}")
            return {
                'found': False,
                'wizard_id': None,
                'image_data': None,
                'image_length': 0
            }