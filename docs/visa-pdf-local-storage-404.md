# visa PDFs: stored on local disk, wiped by every render redeploy (404)

## What was wrong 
'VisaCountry.requirement_pdf' uploads ('admin.visa_add' , 'admin.visa_edit' ) 
saved the file to 'current_app.config["UPLOAD_FOLDER"]' , a local folder on the app server, then linked it at ' / uploads/<filename>'. Every other upload type (package/continent/country images, blog featured images, testimonials) already goes through Cloudinary - visa PDFs were the one exception. Render's web service filesystem is ephemeral: it's rebuilt form docker image on every deployment or restart, so anything written only to local disk disappers. The database kept the old filename, but the file itself no longer existed on the server, so the public "View Requirement" button and the admin PDF links 404'd - with no code change or admin action needed to trigger it, just time passing until the next deploy/restart.

## Fix 
- Added 'ImageUploadService.upload_pdf()' ('image_service.py'), mirroring the existing 'upload_and_compress()' pattern but with 'resource_type="raw"'since Cloudinary's image transform pipeline doesn't apply to PDFs. 
- 'delete _image()' and the shared 'delete_old_image()' helper now take a 'resource_type' parameter so a PDF gets deleted from the right Cloudinary bucket ("raw") instead of silently failing to find it under "image".
- 'visa_add', 'visa_edit', 'visa_delete', and 'remove-visa_pdf' in 'routes/admin.py' now upload/delete through Cloudinary instead of the local 'UPLOAD_FOLDER'.
- Removed the now-dead 'uuid' and 'secure_filename'/'os' usage that existed only to generate and sanitize  the local filename.
- Updated the 3 templates that hardcoded '/uploads/<filemame>' ('packages /visa.html', 'admin/visa.html', 'admin/edit_visa.html') to detect a full Cloudinary URL vs. a legacy local filename, so any already-broken entries don't throw template errors and any admin who re-uploads gets a working link immediately.

## Why the fix is correct 
This mirrors how every other upload type in the app already works - same 'ImageUploadService', same Cloudinary account, same 'delete_old_image' call sites - so visa PDFs now survive redeploys the same way package/country/blog images already do. 8 new tests in 'test/test_admin_visa.py' cover the upload-success, upload-failure, and delete paths, including asserting 'resource_type="raw" is passed on every delete call site. Full suite: 565 passed (up from 557; 2 pre-existing failures in 'TestCloudinarySignature' are a missing CLOUDINARY_API_SECRET' env var in the sandbox this was verified in unrelated to this change). 

Existing visa entries that already show a dead PDF link can't be recovered automatically - the local files behind them are already gone. An admin needs to re-upload each affected country's requirments PDF once after this deploys; from then on it'll persist through redeploys.