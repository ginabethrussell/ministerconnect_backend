# Minister Connect Backend

## API Endpoints

### Candidate Registration

- `POST /api/candidates/register/`
  - Registers a new candidate user.
  - **Required fields:** `invite_code`, `email`, `password`, `first_name`, `last_name`
  - **Example request:**
    ```json
    {
      "invite_code": "CANDIDATE2024",
      "email": "candidate@example.com",
      "password": "securepassword",
      "first_name": "Jane",
      "last_name": "Doe"
    }
    ```
  - **Response:**
    ```json
    { "detail": "Registration successful. Please log in." }
    ```

### Profile Endpoints

- `GET /api/profile/me/` — Retrieve the authenticated user's profile.
- `PATCH /api/profile/me/` — Update fields on the authenticated user's profile.
- `PUT /api/profile/me/` — Replace the authenticated user's profile.
- `POST /api/profile/reset/` — Reset the profile to a blank draft (removes resume and clears fields).

#### Profile Status Logic

- **Draft:** Can be saved with incomplete fields. Minimal validation is enforced.
- **Pending:** All required fields (`phone`, `street_address`, `city`, `state`, `zipcode`, `resume`) must be filled to submit.

#### Resume Upload

- Field: `resume` (file, PDF, max 5MB)
- To replace, upload a new file; to remove, use the reset endpoint.
- Resume is deleted from storage and DB reference when profile is reset.

#### Example PATCH request (to submit as pending):
```json
{
  "status": "pending",
  "phone": "+15551234567",
  "street_address": "123 Main St",
  "city": "Lexington",
  "state": "KY",
  "zipcode": "40502",
  "resume": <PDF file>
}
```

#### Example response for GET /api/profile/me/
```json
{
  "id": 1,
  "phone": "+15551234567",
  "invite_code": 2,
  "invite_code_string": "CANDIDATE2024",
  "street_address": "123 Main St",
  "city": "Lexington",
  "state": "KY",
  "zipcode": "40502",
  "status": "draft",
  "resume": "https://your-bucket.s3.amazonaws.com/resumes/GBR_RESUME.pdf",
  "video_url": null,
  "placement_preferences": ["Youth Ministry"],
  "submitted_at": null,
  "created_at": "2025-07-19T18:20:02.272847Z",
  "updated_at": "2025-07-19T18:37:23.310730Z",
  "user": 17
}
```

---

## Profile Reset

- `POST /api/profile/reset/` — Resets the profile to a blank draft, removes resume from storage and DB, and clears all fields except user and invite_code.
- Only the authenticated user can reset their own profile.
- **Response:**
  ```json
  {
    "detail": "Profile reset to draft successfully.",
    "profile": { ...profile fields... }
  }
  ```

---

## Status Table

| Status   | Validation Level         | User Experience                |
|----------|-------------------------|--------------------------------|
| draft    | Minimal (allow partial) | Save progress, return later    |
| pending  | Strict (all required)   | Must complete all fields       | 