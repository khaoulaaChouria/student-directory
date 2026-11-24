# Student Directory – CS353 Lab 10

A small Flask + SQLite app, packaged in Docker, built by GitHub Actions CI/CD, and deployed to a local Kubernetes cluster (Docker Desktop).

## Run locally (no Docker)

```bash
pip install -r requirements.txt
DB_PATH=./students.db APP_TITLE="Student Directory" python app.py
# open http://localhost:5000
```

## Build and run the container

```bash
docker build -t student-directory:local .
docker run --rm -p 5000:5000 -v sd-data:/data student-directory:local
```

## CI/CD (GitHub Actions)

The workflow is in `.github/workflows/ci.yml`:

- `test`: installs dependencies and runs a smoke test (GET /, POST /add, record visible).
- `build-and-push`: on pushes to `main` only, builds the image and pushes `ghcr.io/<owner>/student-directory:latest` and `:<commit-sha>` to GitHub Container Registry.

It authenticates with the built-in `GITHUB_TOKEN`, so no secret is stored in the repository.

## Deploy to Docker Desktop Kubernetes

1. Replace `OWNER` in `k8s/deployment.yaml` with your lowercase GitHub username or organization.
2. Create the pull secret for GHCR (do not commit it). Use a GitHub personal access token with the `read:packages` scope:

   ```bash
   kubectl create secret docker-registry ghcr-pull \
     --docker-server=ghcr.io \
     --docker-username=<github-user> \
     --docker-password=<github-PAT-read:packages>
   ```

   Alternatively, make the package public in GitHub (Packages → package settings) and skip this step; then remove the `imagePullSecrets` block from `deployment.yaml`.

3. Apply the manifests:

   ```bash
   kubectl apply -f k8s/pv.yaml -f k8s/pvc.yaml
   kubectl apply -f k8s/configmap.yaml -f k8s/secret.yaml
   kubectl apply -f k8s/deployment.yaml -f k8s/service.yaml
   kubectl apply -f k8s/rbac.yaml
   ```

4. Open the app at `http://localhost:30080` (NodePort), or use `kubectl port-forward svc/student-directory 8080:80`.

## Verification commands

```bash
kubectl get deploy,pod,svc,cm,pvc
kubectl get secret student-directory-secret          # metadata only; never print the value
kubectl describe pod -l app=student-directory | grep -A3 "Environment"
kubectl auth can-i delete pods --as=student-reader    # expected: no
kubectl auth can-i list pods --as=student-reader      # expected: yes
```

## Persistence and backup (Part H)

```powershell
$POD = kubectl get pods -l app=student-directory -o jsonpath="{.items[0].metadata.name}"
kubectl exec $POD -- python -c "import sqlite3; src=sqlite3.connect('/data/students.db'); dst=sqlite3.connect('/tmp/students-backup.db'); src.backup(dst); dst.close(); src.close()"
kubectl cp "${POD}:/tmp/students-backup.db" ".\students-backup.db"
kubectl exec $POD -- rm /data/students.db
kubectl cp ".\students-backup.db" "${POD}:/data/students.db"
```

Note: the app image runs as a non-root user with a read-only root filesystem. `/data` is the PVC and `/tmp` is an emptyDir, so these commands work. If `kubectl exec ... rm` is refused, the pod's `/data` mount may be read-only; check the PVC access mode.

## Security measures implemented

- Non-sensitive config in a ConfigMap; a dummy token in a Secret (never printed).
- Non-root user (UID 10001), `allowPrivilegeEscalation: false`, `readOnlyRootFilesystem: true`, all capabilities dropped, RuntimeDefault seccomp profile.
- Read-only Role and RoleBinding for a test user.
- CI/CD uses the scoped `GITHUB_TOKEN`; any extra credentials go in GitHub Actions secrets, not in code.

## Limitations

- SQLite with a single replica only.
- `hostPath` is for the local teaching demo, not production.
- Persistent storage is not a backup.
