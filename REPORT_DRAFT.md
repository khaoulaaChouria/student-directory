# CS353 – Lab 10 Mini-Project Report (draft)

**Student:** Aziz
**Repository:** `https://github.com/OWNER/student-directory` (replace OWNER with your GitHub username)

> Replace the placeholders marked `[...]` with your own screenshots, outputs and observations. Keep the report within 5 pages.

## 1. Architecture

Browser → Kubernetes Service (NodePort 30080) → Deployment (1 replica) → Flask Pod. The Pod receives `APP_TITLE` from a ConfigMap, a token from a Secret, and mounts a PVC at `/data`, where `students.db` is stored. The PVC is bound to a hostPath PV. The image is built and pushed by GitHub Actions to GitHub Container Registry (GHCR).

## 2. Steps and key outputs

| Part | Action | Evidence |
|---|---|---|
| A | Flask + SQLite app, APP_TITLE and DB_PATH from env | [screenshot of app] |
| B | `docker build`, `docker run -p 5000:5000` | [output] |
| C | `.github/workflows/ci.yml`: test → build and push to GHCR | [pipeline screenshot] [registry screenshot] |
| D | Deployment + Service, imagePullSecret `ghcr-pull` | [kubectl get deploy,pod,svc] |
| E | ConfigMap, Secret (metadata only), PV/PVC Bound, persistence test | [pvc status] [record before/after pod delete] |
| F1 | CI/CD variables masked and protected | [variable list, values hidden] |
| F2 | Image scan | [scan summary by severity] |
| F3 | RBAC read-only Role/RoleBinding | [`kubectl auth can-i` output] |
| F4 | securityContext | [`kubectl get pod -o yaml` extract] |
| H | Backup, delete, restore | [record list after restore] |

## 3. Problems encountered and solutions

[Describe each real problem and its fix, e.g. runner not supporting DinD → switched to Kaniko; PVC not binding → storageClassName/volumeName mismatch; read-only root filesystem → added emptyDir at /tmp.]

## 4. Answers to the questions

1. **Why build a Docker image instead of running on the host?** The image packages the app with its exact dependencies and runtime, so it runs the same way on any machine or cluster. It also isolates the process and makes deployments repeatable and versioned.

2. **Role of the CI/CD pipeline?** It automates testing, building and publishing. Every commit is checked by the smoke test, and only a successful build is pushed to the registry, so the cluster always pulls a tested, versioned image.

3. **ConfigMap vs Secret?** A ConfigMap stores ordinary, non-sensitive configuration (e.g. `APP_TITLE`). A Secret stores sensitive values (tokens, passwords), and Kubernetes handles it with stricter access controls and optional encryption at rest.

4. **Why is Base64 not enough to protect a Secret?** Base64 is an encoding, not encryption. Anyone able to read the Secret object can decode it instantly, so protection depends on RBAC and encryption at rest.

5. **Relationship between PV, PVC and Pod?** The PV is the actual storage resource. The PVC is a claim that binds to a suitable PV. The Pod references the PVC as a volume and mounts it at `/data`. The data survives because it lives in the PV, not in the Pod.

6. **How did you verify that data survives Pod recreation?** [Add a student, run `kubectl delete pod -l app=student-directory`, wait for the replacement to be Ready, and check the record is still listed. Describe the actual result.]

7. **Why run as non-root?** If an attacker compromises the application, a non-root process has far fewer privileges on the container and host, which limits the damage.

8. **Principle of least privilege in RBAC?** Each subject receives only the verbs and resources it needs. Here the reader role allows only get, list and watch, so it cannot create, modify or delete resources.

9. **What did the scan show, and what would you improve?** [Summarise the counts by severity from your scan. Propose concrete fixes, such as updating the `python:3.12-slim` base image to the latest patch release, upgrading Flask/gunicorn, and rescanning.]

10. **Does a clean scan guarantee security?** No. A scanner only detects known vulnerabilities in its database. It cannot find zero-days, logic flaws, misconfigurations or leaked secrets, so scanning is one layer among several.

11. **Why copy the backup to your computer instead of keeping it in the Pod?** A copy inside the same Pod and PVC is lost with the storage it protects. Keeping it outside means it survives the loss of the Pod, the PVC or the cluster.

12. **Persistent storage vs backup?** Persistent storage keeps data available across Pod restarts. It does not protect against deletion, corruption or human error, which a backup does, because it is a separate, point-in-time copy.

13. **Why store backups separately from the original data?** If the same failure (deletion, disk failure, ransomware, a bad account) hits both copies, the backup is useless. Separation is the reason for the 3-2-1 rule.

14. **Why test the restore?** An untested backup may be corrupt or incomplete. A restore test proves that the data can actually be recovered within an acceptable time.

## 5. Conclusion

[Two or three sentences on what worked, what you would do differently in production (automated backups, image signing, network policies, a managed database).]
