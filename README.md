# Document Processing Platform

## Database Schema

The application uses 3 tables:

### 1. `users`

- This table stores user related data with the following fields:

|Column|Type|Constraints|Description|
|---|---|---|---|
|id|BigInteger|PRIMARY KEY|Unique identifier for a user record|
|email|String(255)|UNIQUE, NOT NULL|Email address of the user created on sign up|
|password_hash|String(255)|NOT NULL|Password hash created of the user password using argon2-cffi|
|created_at|DateTime|NOT NULL|Timezone-aware timestamp of user account creation|

### 2. `documents`

- This table stores all the uploaded documents with following fields:

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

> - `user_id` is a foreign key referencing `users.id`.
> - When a user record is deleted, all the documents referencing that `user_id` are deleted as well (ON DELETE CASCADE).

#### `document_status` 

- Defines 4 valid states for a document.

|State|Description|
|---|---|
|UPLOADED|The document is successfully uploaded in storage (as a file) as well as in database (as a record)|
|PROCESSING|The document is in one of these stages - (Text Extraction, Chunking, or Embedding Generation)|
|COMPLETED|The document's text extraction, chunking and embedding generation are completed.|
|FAILED|Failed to process document at either of these stages - (Text Extraction, Chunking, or Embedding Generation)|


### 3. `document_chunks`

- This table stores the extracted text and meta data for each chunk of the document's extracted_text.

|Column|Type|Constraints|Description|
|---|---|---|---|
|id|BigInteger|PRIMARY KEY|Unique identifier for each chunk|
|document_id|BigInteger|FOREIGN KEY, NOT NULL|Refers to document id of the document to which a chunk belongs to|
|chunk_index|Integer|NOT NULL|Index of the chunk relative to a document|
|content|Text|NOT NULL|Extracted text of the chunk|
|embedding|Vector(384)|---|Vector embedding of the extracted text|
|page_no|Integer|NOT NULL|Page number on which the chunk exists in the document|

> - `document_id` is a foreign key referencing `documents.id`.
> - When a document record is deleted, all the chunks referencing that `document_id` are deleted as well (ON DELETE CASCADE).
> - UNIQUE(`document_id`, `chunk_index`) constraint exists to prevent duplicate insertion of the same chunk in the table.
