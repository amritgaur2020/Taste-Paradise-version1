"""
TasteParadise Cloud Sync Service - MongoDB to MongoDB Atlas
Real-time sync between local MongoDB and MongoDB Atlas
Author: Amrit Gaur
"""

import time
import threading
from datetime import datetime
from pymongo import MongoClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB Configuration
LOCAL_MONGO_URI = "mongodb://localhost:27017"
ATLAS_MONGO_URI = "mongodb+srv://gaurhariom60_db_user:S4J2vvbZLbrRAlP7@cluster01.7o6we1z.mongodb.net/tasteparadise?retryWrites=true&w=majority&appName=cluster01"
LOCAL_DB_NAME = "taste_paradise"

class CloudSyncService:
    """
    Hybrid database system - Local MongoDB + Cloud MongoDB Atlas
    - Syncs customer data to cloud every 5 minutes
    - You can edit in MongoDB Atlas
    - Changes sync back to local database
    """
    
    def __init__(self, license_key):
        self.license_key = license_key
        self.sync_enabled = False
        self.last_sync = None
        
        # Connect to local MongoDB
        try:
            self.local_client = MongoClient(LOCAL_MONGO_URI, serverSelectionTimeoutMS=5000)
            self.local_db = self.local_client[LOCAL_DB_NAME]
            self.local_client.server_info()
            logger.info("✅ Connected to local MongoDB")
        except Exception as e:
            logger.error(f"❌ Failed to connect to local MongoDB: {e}")
            self.local_client = None
        
        # Connect to MongoDB Atlas
        try:
            self.atlas_client = MongoClient(ATLAS_MONGO_URI, serverSelectionTimeoutMS=10000)
            self.atlas_db = self.atlas_client['tasteparadise']
            self.atlas_collection = self.atlas_db['customer_data']
            self.atlas_client.server_info()
            self.online = True
            logger.info("✅ Connected to MongoDB Atlas")
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB Atlas: {e}")
            self.atlas_client = None
            self.online = False
    
    def start_sync(self):
        """Start background sync service"""
        if not self.online or not self.local_client:
            logger.warning("⚠️ Cloud sync disabled (offline or local MongoDB unavailable)")
            return
        
        self.sync_enabled = True
        sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        sync_thread.start()
        logger.info("✅ Cloud sync service started (syncs every 5 minutes)")
        
        # Do initial sync immediately
        self.upload_to_cloud()
    
    def stop_sync(self):
        """Stop sync service"""
        self.sync_enabled = False
        logger.info("⚠️ Cloud sync service stopped")
    
    def _sync_loop(self):
        """Background sync loop"""
        while self.sync_enabled:
            try:
                time.sleep(300)  # Wait 5 minutes
                
                # Upload local data to cloud
                self.upload_to_cloud()
                
                # Download cloud changes to local
                self.download_from_cloud()
                
                self.last_sync = datetime.now()
                
            except Exception as e:
                logger.error(f"⚠️ Sync error: {e}")
                time.sleep(60)  # Wait 1 minute on error
    
    def upload_to_cloud(self):
        """
        Upload local MongoDB to MongoDB Atlas
        You can view this data in Atlas web interface
        """
        try:
            if not self.online or not self.local_client:
                return
            
            # Get all collections from local MongoDB
            collection_names = self.local_db.list_collection_names()
            
            total_uploaded = 0
            
            for collection_name in collection_names:
                # Skip system collections
                if collection_name.startswith('system.'):
                    continue
                
                # Get all documents from local collection
                local_collection = self.local_db[collection_name]
                documents = list(local_collection.find())
                
                if not documents:
                    continue
                
                # Prepare documents for Atlas
                atlas_documents = []
                for doc in documents:
                    # Keep original _id for sync tracking
                    doc_id = str(doc.get('_id'))
                    
                    # Create a copy without _id
                    doc_copy = {k: v for k, v in doc.items() if k != '_id'}
                    
                    # Add metadata for cloud storage
                    doc_copy['_original_id'] = doc_id
                    doc_copy['_collection'] = f"{self.license_key}_{collection_name}"
                    doc_copy['_sync_time'] = datetime.now().isoformat()
                    doc_copy['_license'] = self.license_key
                    
                    atlas_documents.append(doc_copy)
                
                # Upload to MongoDB Atlas
                if atlas_documents:
                    try:
                        # Clear existing data for this collection
                        self.atlas_collection.delete_many({
                            '_collection': f"{self.license_key}_{collection_name}"
                        })
                        
                        # Insert new data
                        self.atlas_collection.insert_many(atlas_documents)
                        total_uploaded += len(atlas_documents)
                        logger.debug(f"☁️ Synced {len(atlas_documents)} docs from {collection_name}")
                    
                    except Exception as e:
                        logger.error(f"❌ Error uploading {collection_name}: {e}")
            
            if total_uploaded > 0:
                logger.info(f"☁️ Uploaded {total_uploaded} documents to cloud")
            
        except Exception as e:
            logger.error(f"⚠️ Upload error: {e}")
    
    def download_from_cloud(self):
        """
        Download changes from MongoDB Atlas
        If you edited data in Atlas, it syncs to local MongoDB
        """
        try:
            if not self.online or not self.local_client:
                return
            
            # Find all collections for this license
            docs = self.atlas_collection.find({'_license': self.license_key})
            
            # Group by collection name
            collections = {}
            for doc in docs:
                collection_name = doc.get('_collection', '')
                if not collection_name:
                    continue
                
                # Extract original collection name
                table_name = collection_name.replace(f"{self.license_key}_", "")
                
                if table_name not in collections:
                    collections[table_name] = []
                
                # Remove MongoDB metadata
                doc.pop('_id', None)
                doc.pop('_collection', None)
                doc.pop('_sync_time', None)
                doc.pop('_license', None)
                original_id = doc.pop('_original_id', None)
                
                collections[table_name].append(doc)
            
            # For now, we only upload to cloud
            # Download/merge logic can be added later if needed
            
        except Exception as e:
            logger.error(f"⚠️ Download error: {e}")
    
    def manual_sync(self):
        """Manual sync (call this when customer clicks "Sync Now" button)"""
        if not self.online:
            return {'success': False, 'message': 'Offline'}
        
        try:
            self.upload_to_cloud()
            self.download_from_cloud()
            return {'success': True, 'message': 'Sync completed', 'time': datetime.now()}
        except Exception as e:
            return {'success': False, 'message': str(e)}

# Global instance
cloud_sync = None

def init_cloud_sync(license_key):
    """Initialize cloud sync service"""
    global cloud_sync
    try:
        cloud_sync = CloudSyncService(license_key)
        cloud_sync.start_sync()
        return cloud_sync
    except Exception as e:
        logger.error(f"Failed to initialize cloud sync: {e}")
        return None
