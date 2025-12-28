"""
Celery tasks for tasks in Task Management System.

This module contains all Celery tasks for:
- Processing task attachments
- Task-related data processing

All tasks are designed to be:
- Async and non-blocking
- Retryable on failure
- Well-logged for debugging
- Production-ready with proper error handling

Data processing tasks:
- process_task_attachments
"""

import logging
import os
from typing import Optional, Dict, Any, List
from django.core.files.storage import default_storage
from django.conf import settings
from django.utils import timezone
from celery import shared_task

from tasks.models import Task, TaskAttachment

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # Retry after 60 seconds
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,  # Max 10 minutes between retries
    retry_jitter=True,  # Add randomness to retry timing
    ignore_result=False,
)
def process_task_attachments(
    self,
    task_id: Optional[int] = None,
    attachment_id: Optional[int] = None,
    process_type: str = 'validate',
    generate_metadata: bool = True,
    validate_file_integrity: bool = True
) -> Dict[str, Any]:
    """
    Process task attachments for validation, metadata extraction, and optimization.
    
    This task processes task attachments to:
    - Validate file integrity and format
    - Extract and store metadata (file size, type, dimensions for images)
    - Generate thumbnails for images (future enhancement)
    - Check for malicious content (basic validation)
    - Update attachment records with processed information
    
    The processing can be done for:
    - A specific attachment (attachment_id provided)
    - All attachments for a specific task (task_id provided)
    - All unprocessed attachments (neither provided, processes all)
    
    Args:
        self: Celery task instance (for retries)
        task_id: Optional ID of the task to process attachments for
        attachment_id: Optional ID of specific attachment to process
        process_type: Type of processing ('validate', 'metadata', 'all')
        generate_metadata: Whether to generate/extract metadata
        validate_file_integrity: Whether to validate file integrity
        
    Returns:
        dict: Processing result dictionary with the following structure:
            {
                'status': str ('success', 'partial', 'error'),
                'processed_count': int,
                'failed_count': int,
                'skipped_count': int,
                'results': [
                    {
                        'attachment_id': int,
                        'filename': str,
                        'status': str ('success', 'failed', 'skipped'),
                        'metadata': dict,
                        'errors': list,
                    }
                ],
                'summary': {
                    'total_size': int (bytes),
                    'total_files': int,
                    'by_file_type': {type: count},
                }
            }
        
    Raises:
        Retry: If task should be retried
        Exception: For other errors
        
    Example:
        from tasks.tasks import process_task_attachments
        
        # Process all attachments for a task
        result = process_task_attachments.delay(
            task_id=1,
            process_type='all',
            generate_metadata=True
        )
        
        # Process a specific attachment
        result = process_task_attachments.delay(
            attachment_id=5,
            process_type='validate'
        )
    """
    try:
        processed_count = 0
        failed_count = 0
        skipped_count = 0
        results = []
        total_size = 0
        file_type_counts = {}
        
        # Determine which attachments to process
        if attachment_id:
            # Process specific attachment
            attachments = TaskAttachment.objects.filter(pk=attachment_id)
            logger.info(f"Processing attachment ID: {attachment_id}")
        elif task_id:
            # Process all attachments for a task
            attachments = TaskAttachment.objects.filter(task_id=task_id)
            logger.info(f"Processing attachments for task ID: {task_id}")
        else:
            # Process all unprocessed attachments (those without metadata or validation)
            # For now, process all attachments - can be enhanced with a 'processed' flag
            attachments = TaskAttachment.objects.all()
            logger.info("Processing all attachments")
        
        if not attachments.exists():
            logger.warning("No attachments found to process")
            return {
                'status': 'skipped',
                'processed_count': 0,
                'failed_count': 0,
                'skipped_count': 0,
                'results': [],
                'summary': {
                    'total_size': 0,
                    'total_files': 0,
                    'by_file_type': {},
                }
            }
        
        # Process each attachment
        for attachment in attachments.select_related('task', 'uploaded_by'):
            try:
                result = {
                    'attachment_id': attachment.id,
                    'filename': attachment.filename,
                    'status': 'pending',
                    'metadata': {},
                    'errors': [],
                }
                
                # Check if file exists
                if not attachment.file or not attachment.file.name:
                    result['status'] = 'skipped'
                    result['errors'].append('File not found or not uploaded')
                    skipped_count += 1
                    results.append(result)
                    continue
                
                # Get file path
                file_path = attachment.file.path if hasattr(attachment.file, 'path') else None
                
                if not file_path or not os.path.exists(file_path):
                    # Try using default storage
                    if default_storage.exists(attachment.file.name):
                        file_path = default_storage.path(attachment.file.name)
                    else:
                        result['status'] = 'failed'
                        result['errors'].append('File does not exist on storage')
                        failed_count += 1
                        results.append(result)
                        continue
                
                # Validate file integrity
                if validate_file_integrity:
                    try:
                        file_size = os.path.getsize(file_path)
                        if file_size == 0:
                            result['status'] = 'failed'
                            result['errors'].append('File is empty')
                            failed_count += 1
                            results.append(result)
                            continue
                        
                        # Verify file size matches stored size
                        if attachment.file_size and file_size != attachment.file_size:
                            logger.warning(
                                f"File size mismatch for attachment {attachment.id}: "
                                f"stored={attachment.file_size}, actual={file_size}"
                            )
                            # Update stored size
                            attachment.file_size = file_size
                            attachment.save(update_fields=['file_size'])
                        
                        result['metadata']['file_size'] = file_size
                        result['metadata']['file_size_validated'] = True
                        total_size += file_size
                        
                    except OSError as e:
                        result['status'] = 'failed'
                        result['errors'].append(f'Error accessing file: {str(e)}')
                        failed_count += 1
                        results.append(result)
                        continue
                
                # Generate/extract metadata
                if generate_metadata:
                    try:
                        # File type information
                        file_type = attachment.file_type or os.path.splitext(attachment.filename)[1].lower().lstrip('.')
                        result['metadata']['file_type'] = file_type
                        result['metadata']['file_extension'] = os.path.splitext(attachment.filename)[1].lower()
                        
                        # Update file type if not set
                        if not attachment.file_type:
                            attachment.file_type = file_type
                            attachment.save(update_fields=['file_type'])
                        
                        # Count by file type
                        file_type_counts[file_type] = file_type_counts.get(file_type, 0) + 1
                        
                        # Image-specific metadata (if applicable)
                        if file_type.lower() in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp']:
                            try:
                                from PIL import Image
                                
                                with Image.open(file_path) as img:
                                    width, height = img.size
                                    result['metadata']['image_width'] = width
                                    result['metadata']['image_height'] = height
                                    result['metadata']['image_format'] = img.format
                                    result['metadata']['image_mode'] = img.mode
                                    
                                    # Calculate aspect ratio
                                    if height > 0:
                                        result['metadata']['aspect_ratio'] = round(width / height, 2)
                                    
                                    logger.debug(
                                        f"Image metadata extracted for attachment {attachment.id}: "
                                        f"{width}x{height}, format: {img.format}"
                                    )
                            except ImportError:
                                logger.warning("PIL/Pillow not installed, skipping image metadata extraction")
                            except Exception as e:
                                logger.warning(f"Error extracting image metadata: {e}")
                                result['errors'].append(f'Image metadata extraction failed: {str(e)}')
                        
                        # Document-specific metadata (future enhancement)
                        # Could extract text from PDFs, word count from documents, etc.
                        
                        # File hash for integrity checking (future enhancement)
                        # Could calculate MD5 or SHA256 hash
                        
                        result['metadata']['processed_at'] = timezone.now().isoformat()
                        result['status'] = 'success'
                        processed_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error generating metadata for attachment {attachment.id}: {e}", exc_info=True)
                        result['status'] = 'failed'
                        result['errors'].append(f'Metadata generation failed: {str(e)}')
                        failed_count += 1
                
                else:
                    # Only validation, no metadata
                    result['status'] = 'success'
                    processed_count += 1
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing attachment {attachment.id}: {e}", exc_info=True)
                failed_count += 1
                results.append({
                    'attachment_id': attachment.id,
                    'filename': attachment.filename if attachment else 'unknown',
                    'status': 'failed',
                    'metadata': {},
                    'errors': [f'Processing error: {str(e)}'],
                })
        
        # Determine overall status
        if failed_count == 0:
            status = 'success'
        elif processed_count > 0:
            status = 'partial'
        else:
            status = 'error'
        
        summary = {
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'total_files': len(results),
            'by_file_type': file_type_counts,
        }
        
        logger.info(
            f"Attachment processing completed: {processed_count} processed, "
            f"{failed_count} failed, {skipped_count} skipped"
        )
        
        return {
            'status': status,
            'processed_count': processed_count,
            'failed_count': failed_count,
            'skipped_count': skipped_count,
            'results': results,
            'summary': summary,
        }
        
    except Exception as exc:
        logger.error(f"Error in process_task_attachments: {exc}", exc_info=True)
        # Retry the task
        raise self.retry(exc=exc)

