"""
Local File Discoverer - Finds local files matching search criteria
"""

from typing import List, Dict, Optional
import os
import glob
from pathlib import Path
import logging
from datetime import datetime


class LocalFileDiscoverer:
    """Discovers local files based on search criteria"""
    
    def __init__(
        self,
        base_directories: Optional[List[str]] = None,
        supported_extensions: Optional[List[str]] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.base_directories = base_directories or []
        self.supported_extensions = supported_extensions or ['pdf', 'md', 'txt', 'docx']
        self.logger = logger or logging.getLogger(__name__)
    
    def discover_files(
        self,
        query_analysis: Dict,
        recursive: bool = True,
        max_files: int = 100
    ) -> List[Dict]:
        """
        Discover local files matching query criteria
        
        Args:
            query_analysis: Results from QueryAnalyzer
            recursive: Whether to search subdirectories
            max_files: Maximum number of files to return
            
        Returns:
            List of file pattern dictionaries
        """
        file_patterns = []
        search_terms = query_analysis.get('search_terms', [])
        
        # Check if local search is indicated
        domain_hints = query_analysis.get('domain_hints', {})
        if not domain_hints.get('local') and not self.base_directories:
            self.logger.debug("Local file search not indicated or no base directories configured")
            return []
        
        # Search each base directory
        for base_dir in self.base_directories:
            if not os.path.exists(base_dir):
                self.logger.warning(f"Base directory does not exist: {base_dir}")
                continue
            
            # Generate file patterns
            patterns = self._generate_file_patterns(base_dir, search_terms, recursive)
            
            # Find matching files
            for pattern_info in patterns:
                matching_files = self._find_matching_files(
                    pattern_info['pattern'],
                    pattern_info['base_directory']
                )
                
                if matching_files:
                    file_patterns.append({
                        'pattern': pattern_info['pattern'],
                        'base_directory': pattern_info['base_directory'],
                        'file_count_estimate': len(matching_files),
                        'supported_formats': self.supported_extensions,
                        'recursive': recursive,
                        'matching_files': matching_files[:max_files]
                    })
        
        self.logger.info(f"Discovered {len(file_patterns)} file patterns")
        
        return file_patterns
    
    def _generate_file_patterns(
        self,
        base_dir: str,
        search_terms: List[str],
        recursive: bool
    ) -> List[Dict]:
        """Generate glob patterns for file search"""
        patterns = []
        
        # For each supported extension
        for ext in self.supported_extensions:
            # Pattern without search terms (all files of this type)
            if recursive:
                pattern = os.path.join(base_dir, '**', f'*.{ext}')
            else:
                pattern = os.path.join(base_dir, f'*.{ext}')
            
            patterns.append({
                'pattern': pattern,
                'base_directory': base_dir,
                'extension': ext
            })
            
            # Pattern with search terms in filename
            for term in search_terms:
                if recursive:
                    pattern = os.path.join(base_dir, '**', f'*{term}*.{ext}')
                else:
                    pattern = os.path.join(base_dir, f'*{term}*.{ext}')
                
                patterns.append({
                    'pattern': pattern,
                    'base_directory': base_dir,
                    'extension': ext,
                    'search_term': term
                })
        
        return patterns
    
    def _find_matching_files(self, pattern: str, base_dir: str) -> List[str]:
        """Find files matching a glob pattern"""
        try:
            # Use glob to find matching files
            matching_files = glob.glob(pattern, recursive=True)
            
            # Filter to ensure they're files (not directories)
            matching_files = [f for f in matching_files if os.path.isfile(f)]
            
            self.logger.debug(f"Found {len(matching_files)} files matching pattern: {pattern}")
            
            return matching_files
            
        except Exception as e:
            self.logger.error(f"Error finding files with pattern {pattern}: {str(e)}")
            return []
    
    def get_file_metadata(self, filepath: str) -> Dict:
        """
        Get metadata for a file
        
        Args:
            filepath: Path to the file
            
        Returns:
            Dictionary with file metadata
        """
        try:
            stat_info = os.stat(filepath)
            
            return {
                'filepath': filepath,
                'filename': os.path.basename(filepath),
                'extension': os.path.splitext(filepath)[1][1:],  # Remove leading dot
                'size_bytes': stat_info.st_size,
                'size_kb': stat_info.st_size // 1024,
                'created_time': datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                'modified_time': datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                'accessed_time': datetime.fromtimestamp(stat_info.st_atime).isoformat(),
            }
        except Exception as e:
            self.logger.error(f"Error getting metadata for {filepath}: {str(e)}")
            return {'filepath': filepath, 'error': str(e)}
    
    def scan_directory(
        self,
        directory: str,
        recursive: bool = True,
        extensions: Optional[List[str]] = None
    ) -> Dict:
        """
        Scan a directory for files
        
        Args:
            directory: Directory to scan
            recursive: Whether to scan subdirectories
            extensions: File extensions to include (None for all)
            
        Returns:
            Dictionary with scan results
        """
        if not os.path.exists(directory):
            return {
                'directory': directory,
                'error': 'Directory does not exist',
                'files': []
            }
        
        extensions = extensions or self.supported_extensions
        files = []
        
        try:
            if recursive:
                # Walk directory tree
                for root, dirs, filenames in os.walk(directory):
                    for filename in filenames:
                        ext = os.path.splitext(filename)[1][1:]  # Remove leading dot
                        if ext in extensions:
                            filepath = os.path.join(root, filename)
                            files.append(self.get_file_metadata(filepath))
            else:
                # Only scan top-level directory
                for filename in os.listdir(directory):
                    filepath = os.path.join(directory, filename)
                    if os.path.isfile(filepath):
                        ext = os.path.splitext(filename)[1][1:]
                        if ext in extensions:
                            files.append(self.get_file_metadata(filepath))
            
            return {
                'directory': directory,
                'file_count': len(files),
                'files': files,
                'recursive': recursive,
                'extensions': extensions
            }
            
        except Exception as e:
            self.logger.error(f"Error scanning directory {directory}: {str(e)}")
            return {
                'directory': directory,
                'error': str(e),
                'files': []
            }
    
    def filter_by_date(
        self,
        files: List[Dict],
        max_age_days: Optional[int] = None,
        prefer_fresh: bool = False
    ) -> List[Dict]:
        """
        Filter files by date criteria
        
        Args:
            files: List of file metadata dictionaries
            max_age_days: Maximum age in days
            prefer_fresh: Whether to prefer fresher files
            
        Returns:
            Filtered list of files
        """
        if not files:
            return []
        
        now = datetime.now()
        filtered_files = []
        
        for file_info in files:
            try:
                modified_time = datetime.fromisoformat(file_info['modified_time'])
                age_days = (now - modified_time).days
                
                # Filter by max age
                if max_age_days is not None and age_days > max_age_days:
                    continue
                
                file_info['age_days'] = age_days
                filtered_files.append(file_info)
                
            except Exception as e:
                self.logger.warning(f"Error processing file date for {file_info.get('filepath')}: {str(e)}")
                continue
        
        # Sort by freshness if preferred
        if prefer_fresh:
            filtered_files.sort(key=lambda x: x.get('age_days', float('inf')))
        
        return filtered_files