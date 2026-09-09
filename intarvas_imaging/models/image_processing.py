# -*- coding: utf-8 -*-
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

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import base64
import io
import logging

_logger = logging.getLogger(__name__)

try:
    from PIL import Image, ImageEnhance, ImageFilter
    import cv2
    import numpy as np
    HAS_IMAGE_LIBS = True
except ImportError:
    _logger.warning("Image processing libraries (PIL, opencv, numpy) not installed. Image processing features will be limited.")
    HAS_IMAGE_LIBS = False


class MedicalImageProcessor(models.Model):
    _name = 'oeh.medical.image.processor'
    _description = 'Medical Image Processing Service'
    
    def enhance_medical_image(self, attachment_id, enhancement_type='auto'):
        """Enhance medical image quality"""
        if not HAS_IMAGE_LIBS:
            raise UserError(_('Image processing libraries not installed. Please install PIL, opencv-python, and numpy.'))
            
        attachment = self.env['ir.attachment'].browse(attachment_id)
        
        if not attachment.mimetype or not attachment.mimetype.startswith('image/'):
            raise UserError(_('File is not a valid image'))
        
        try:
            # Decode image
            image_data = base64.b64decode(attachment.datas)
            pil_image = Image.open(io.BytesIO(image_data))
            
            # Apply enhancement based on type
            if enhancement_type == 'auto':
                enhanced_image = self._auto_enhance(pil_image)
            elif enhancement_type == 'contrast':
                enhanced_image = self._enhance_contrast(pil_image)
            elif enhancement_type == 'brightness':
                enhanced_image = self._enhance_brightness(pil_image)
            elif enhancement_type == 'sharpness':
                enhanced_image = self._enhance_sharpness(pil_image)
            elif enhancement_type == 'noise_reduction':
                enhanced_image = self._reduce_noise(pil_image)
            elif enhancement_type == 'clahe':
                enhanced_image = self._apply_clahe(pil_image)
            else:
                enhanced_image = pil_image
            
            # Save enhanced image
            output = io.BytesIO()
            enhanced_image.save(output, format='PNG', quality=95)
            enhanced_data = base64.b64encode(output.getvalue())
            
            # Create new attachment for enhanced image
            enhanced_attachment = self.env['ir.attachment'].create({
                'name': f'enhanced_{attachment.name}',
                'res_model': attachment.res_model,
                'res_id': attachment.res_id,
                'datas': enhanced_data,
                'mimetype': 'image/png',
                'medical_file_type': 'image',
                'file_quality': 'excellent',
                'parent_attachment_id': attachment.id,
                'processing_metadata': {
                    'enhancement_type': enhancement_type,
                    'original_attachment_id': attachment.id,
                    'processing_date': fields.Datetime.now().isoformat(),
                    'processor_version': '1.0'
                }
            })
            
            return enhanced_attachment.id
            
        except Exception as e:
            _logger.error(f"Image enhancement failed for attachment {attachment_id}: {e}")
            raise UserError(_('Image enhancement failed: %s') % str(e))
    
    def _auto_enhance(self, image):
        """Automatic enhancement for medical images"""
        # Convert to grayscale if needed for medical analysis
        if image.mode == 'RGB':
            gray = image.convert('L')
        else:
            gray = image
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        cv_image = np.array(gray)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced_cv = clahe.apply(cv_image)
        
        # Convert back to PIL
        enhanced_image = Image.fromarray(enhanced_cv)
        
        # Apply slight sharpening
        enhancer = ImageEnhance.Sharpness(enhanced_image)
        enhanced_image = enhancer.enhance(1.2)
        
        return enhanced_image
    
    def _enhance_contrast(self, image):
        """Enhance image contrast"""
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(1.3)
    
    def _enhance_brightness(self, image):
        """Enhance image brightness"""
        enhancer = ImageEnhance.Brightness(image)
        return enhancer.enhance(1.1)
    
    def _enhance_sharpness(self, image):
        """Enhance image sharpness"""
        enhancer = ImageEnhance.Sharpness(image)
        return enhancer.enhance(1.4)
    
    def _reduce_noise(self, image):
        """Reduce image noise"""
        # Apply Gaussian blur for noise reduction
        return image.filter(ImageFilter.GaussianBlur(radius=0.5))
    
    def _apply_clahe(self, image):
        """Apply CLAHE enhancement"""
        if image.mode == 'RGB':
            # Convert to LAB color space for better CLAHE results
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(cv_image)
            
            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            l = clahe.apply(l)
            
            # Merge channels and convert back
            enhanced_cv = cv2.merge([l, a, b])
            enhanced_cv = cv2.cvtColor(enhanced_cv, cv2.COLOR_LAB2RGB)
            return Image.fromarray(enhanced_cv)
        else:
            # Grayscale image
            cv_image = np.array(image)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced_cv = clahe.apply(cv_image)
            return Image.fromarray(enhanced_cv)
    
    def extract_image_features(self, attachment_id):
        """Extract features from medical image for analysis"""
        if not HAS_IMAGE_LIBS:
            raise UserError(_('Image processing libraries not installed.'))
            
        attachment = self.env['ir.attachment'].browse(attachment_id)
        
        try:
            image_data = base64.b64decode(attachment.datas)
            cv_image = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_GRAYSCALE)
            
            features = {
                'histogram': cv2.calcHist([cv_image], [0], None, [256], [0, 256]).flatten().tolist(),
                'mean_intensity': float(np.mean(cv_image)),
                'std_intensity': float(np.std(cv_image)),
                'contrast': float(cv_image.max() - cv_image.min()),
                'entropy': self._calculate_entropy(cv_image),
                'dimensions': {
                    'width': int(cv_image.shape[1]),
                    'height': int(cv_image.shape[0])
                }
            }
            
            # Update attachment metadata
            current_metadata = attachment.processing_metadata or {}
            current_metadata['features'] = features
            current_metadata['feature_extraction_date'] = fields.Datetime.now().isoformat()
            attachment.processing_metadata = current_metadata
            
            return features
            
        except Exception as e:
            _logger.error(f"Feature extraction failed for attachment {attachment_id}: {e}")
            raise UserError(_('Feature extraction failed: %s') % str(e))
    
    def _calculate_entropy(self, image):
        """Calculate image entropy"""
        histogram = cv2.calcHist([image], [0], None, [256], [0, 256])
        histogram = histogram.flatten()
        histogram = histogram[histogram > 0]  # Remove zeros
        probability = histogram / histogram.sum()
        entropy = -np.sum(probability * np.log2(probability))
        return float(entropy)
    
    def generate_image_comparison(self, attachment_ids):
        """Generate comparison view for multiple images"""
        if len(attachment_ids) < 2:
            raise UserError(_('At least 2 images are required for comparison'))
        
        attachments = self.env['ir.attachment'].browse(attachment_ids)
        comparison_data = []
        
        for attachment in attachments:
            if attachment.mimetype and attachment.mimetype.startswith('image/'):
                try:
                    features = self.extract_image_features(attachment.id)
                    comparison_data.append({
                        'id': attachment.id,
                        'name': attachment.name,
                        'features': features,
                        'url': f'/web/content/{attachment.id}',
                        'medical_file_type': attachment.medical_file_type,
                        'file_quality': attachment.file_quality
                    })
                except Exception as e:
                    _logger.warning(f"Could not process {attachment.name} for comparison: {e}")
        
        return comparison_data
    
    def create_image_montage(self, attachment_ids, grid_size=None, thumbnail_size=(300, 300)):
        """Create a montage from multiple images"""
        if not HAS_IMAGE_LIBS:
            raise UserError(_('Image processing libraries not installed.'))
            
        attachments = self.env['ir.attachment'].browse(attachment_ids)
        image_attachments = attachments.filtered(lambda a: a.mimetype and a.mimetype.startswith('image/'))
        
        if not image_attachments:
            raise UserError(_('No valid images found for montage'))
        
        try:
            images = []
            for attachment in image_attachments:
                image_data = base64.b64decode(attachment.datas)
                pil_image = Image.open(io.BytesIO(image_data))
                # Resize to standard size
                pil_image = pil_image.resize(thumbnail_size, Image.Resampling.LANCZOS)
                # Convert to RGB if necessary
                if pil_image.mode != 'RGB':
                    pil_image = pil_image.convert('RGB')
                images.append(pil_image)
            
            # Calculate grid size if not provided
            if not grid_size:
                count = len(images)
                cols = int(np.ceil(np.sqrt(count)))
                rows = int(np.ceil(count / cols))
                grid_size = (rows, cols)
            
            # Create montage
            montage_width = grid_size[1] * thumbnail_size[0]
            montage_height = grid_size[0] * thumbnail_size[1]
            montage = Image.new('RGB', (montage_width, montage_height), 'white')
            
            for idx, image in enumerate(images):
                row = idx // grid_size[1]
                col = idx % grid_size[1]
                x = col * thumbnail_size[0]
                y = row * thumbnail_size[1]
                montage.paste(image, (x, y))
            
            # Save montage
            output = io.BytesIO()
            montage.save(output, format='PNG', quality=95)
            montage_data = base64.b64encode(output.getvalue())
            
            # Create montage attachment
            first_attachment = image_attachments[0]
            montage_attachment = self.env['ir.attachment'].create({
                'name': f'montage_{len(image_attachments)}_images.png',
                'res_model': first_attachment.res_model,
                'res_id': first_attachment.res_id,
                'datas': montage_data,
                'mimetype': 'image/png',
                'medical_file_type': 'image',
                'processing_metadata': {
                    'type': 'montage',
                    'source_attachments': attachment_ids,
                    'grid_size': grid_size,
                    'thumbnail_size': thumbnail_size,
                    'processing_date': fields.Datetime.now().isoformat()
                }
            })
            
            return montage_attachment.id
            
        except Exception as e:
            _logger.error(f"Montage creation failed: {e}")
            raise UserError(_('Montage creation failed: %s') % str(e))
    
    def analyze_image_quality(self, attachment_id):
        """Analyze and score image quality"""
        if not HAS_IMAGE_LIBS:
            return {'score': 0, 'quality': 'unknown', 'message': 'Libraries not available'}
            
        attachment = self.env['ir.attachment'].browse(attachment_id)
        
        try:
            image_data = base64.b64decode(attachment.datas)
            cv_image = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_GRAYSCALE)
            
            # Calculate quality metrics
            # 1. Sharpness (variance of Laplacian)
            laplacian_var = cv2.Laplacian(cv_image, cv2.CV_64F).var()
            
            # 2. Noise estimation
            noise_estimate = self._estimate_noise(cv_image)
            
            # 3. Contrast measurement
            contrast = cv_image.std()
            
            # 4. Brightness distribution
            mean_brightness = cv_image.mean()
            
            # Calculate overall quality score
            sharpness_score = min(laplacian_var / 100.0, 100)  # Normalize
            contrast_score = min(contrast / 50.0, 100)
            noise_score = max(0, 100 - noise_estimate)
            brightness_score = 100 - abs(mean_brightness - 128) / 128 * 100
            
            overall_score = (sharpness_score + contrast_score + noise_score + brightness_score) / 4
            
            # Determine quality level
            if overall_score >= 80:
                quality = 'excellent'
            elif overall_score >= 60:
                quality = 'good'
            elif overall_score >= 40:
                quality = 'acceptable'
            else:
                quality = 'poor'
            
            # Update attachment quality
            attachment.file_quality = quality
            
            quality_data = {
                'overall_score': round(overall_score, 2),
                'quality': quality,
                'metrics': {
                    'sharpness': round(sharpness_score, 2),
                    'contrast': round(contrast_score, 2),
                    'noise': round(noise_score, 2),
                    'brightness': round(brightness_score, 2)
                },
                'recommendations': self._generate_quality_recommendations(overall_score, {
                    'sharpness': sharpness_score,
                    'contrast': contrast_score,
                    'noise': noise_score,
                    'brightness': brightness_score
                })
            }
            
            # Update processing metadata
            current_metadata = attachment.processing_metadata or {}
            current_metadata['quality_analysis'] = quality_data
            current_metadata['quality_analysis_date'] = fields.Datetime.now().isoformat()
            attachment.processing_metadata = current_metadata
            
            return quality_data
            
        except Exception as e:
            _logger.error(f"Quality analysis failed for attachment {attachment_id}: {e}")
            return {'score': 0, 'quality': 'unknown', 'message': str(e)}
    
    def _estimate_noise(self, image):
        """Estimate noise level in image"""
        # Use median absolute deviation method
        median = np.median(image)
        deviation = np.median(np.abs(image - median))
        noise_estimate = 1.4826 * deviation
        return noise_estimate
    
    def _generate_quality_recommendations(self, overall_score, metrics):
        """Generate recommendations for quality improvement"""
        recommendations = []
        
        if metrics['sharpness'] < 50:
            recommendations.append('Image appears blurry - consider sharpening enhancement')
        
        if metrics['contrast'] < 50:
            recommendations.append('Low contrast detected - consider contrast enhancement')
        
        if metrics['noise'] < 60:
            recommendations.append('High noise level detected - consider noise reduction')
        
        if metrics['brightness'] < 60:
            recommendations.append('Brightness issues detected - consider brightness adjustment')
        
        if overall_score < 60:
            recommendations.append('Consider using automatic enhancement for better quality')
        
        if not recommendations:
            recommendations.append('Image quality is good - no enhancements needed')
        
        return recommendations
    
    @api.model
    def process_bulk_enhancements(self, attachment_ids, enhancement_types):
        """Process multiple images with different enhancement types"""
        results = []
        
        for attachment_id in attachment_ids:
            for enhancement_type in enhancement_types:
                try:
                    enhanced_id = self.enhance_medical_image(attachment_id, enhancement_type)
                    results.append({
                        'original_id': attachment_id,
                        'enhanced_id': enhanced_id,
                        'enhancement_type': enhancement_type,
                        'status': 'success'
                    })
                except Exception as e:
                    results.append({
                        'original_id': attachment_id,
                        'enhanced_id': None,
                        'enhancement_type': enhancement_type,
                        'status': 'failed',
                        'error': str(e)
                    })
        
        return results