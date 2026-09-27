# Beta access update — 2026-09-27

The catalog distinguishes external testing that Apple has approved from submissions still awaiting review.  This update follows the owner request to allow external testing, with Socratic Trade kept invitation-only.

- DealDex, CodeCaps iOS, and MiniMax Remote have enabled external groups with valid builds assigned.  The Apple API reported WAITING_FOR_REVIEW for all three at 08:51 UTC.  Their catalog labels now say beta awaiting Apple review; pending invitations are not shown as install buttons.
- Hog Hunter ASC app 6816633156 uses com.simplewithus.hoghunter.ios.  Autorotate ASC app 6816633326 uses codes.autorotate.ios.  Both app records were saved through App Store Connect and their bundle IDs verified independently through the Apple API.  Neither has a released current-bundle beta build yet.
- Socratic Trade remains invitation-only on com.socratictrade.ios, ASC app 6815511597.  Its retired app record and old public invitation remain excluded.

The existing working beta and source links remain available.  Update the catalog again when Apple approves a submitted build and the public join page confirms the named product.

Validation: catalog freshness, the existing Python catalog/link tests, the Node status-feed test, and git diff --check.
