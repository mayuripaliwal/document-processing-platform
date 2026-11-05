# Document Processing Platform

## Database Schema

The application uses 3 tables:

### `documents`

This table stores all the uploaded documents with following fields:

|Column|Type|Constraints|Description|
|---|---|---|---|
|id|BigInteger|PRIMARY KEY|Unique identifier for documents|
|user_id | BigInteger | FOREIGN KEY, NOT NULL | References the user_id of the user to whom the document belongs to|
|file_name | String(255) | NOT NULL | The file name of the file uploaded by the user|
|stored_file_name | String(255) | UNIQUE, NOT NULL | Unique file name generated using uuid4 to prevent file name collisions|
|mime_type|String(100)|NOT NULL|File type (eg: application/pdf)|
|file_size|BigInteger|NOT NULL|File size of the document in bytes|
|storage_path|Text|NOT NULL|Full storage path of stored file|
|created_at|DateTime|NOT NULL, DEFAULT NOW()|Timezone-aware timestamp when document is uploaded|
|extracted_text|Text|---|Text extracted from the document|
|document_status|Enum(DocumentStatus)|NOT NULL|Status of the document in the document processing pipeline|