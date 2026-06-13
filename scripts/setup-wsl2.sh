#!/usr/bin/env bash
# WSL2 toolchain setup for RunGuard Phase 7
# Run once: bash scripts/setup-wsl2.sh
set -euo pipefail

ARCH=$(dpkg --print-architecture)   # amd64 or arm64
echo "==> Detected arch: $ARCH"

# ── System deps ──────────────────────────────────────────────────────────────
sudo apt-get update -qq
sudo apt-get install -y curl gnupg lsb-release apt-transport-https ca-certificates unzip

# ── kubectl ──────────────────────────────────────────────────────────────────
echo "==> Installing kubectl..."
curl -fsSL "https://pkgs.k8s.io/core:/stable:/v1.31/deb/Release.key" \
  | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.31/deb/ /" \
  | sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update -qq && sudo apt-get install -y kubectl

# ── Helm ─────────────────────────────────────────────────────────────────────
echo "==> Installing Helm..."
curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# ── ArgoCD CLI ───────────────────────────────────────────────────────────────
echo "==> Installing ArgoCD CLI..."
ARGOCD_VERSION=$(curl -s https://api.github.com/repos/argoproj/argo-cd/releases/latest \
  | grep '"tag_name"' | cut -d'"' -f4)
curl -fsSL "https://github.com/argoproj/argo-cd/releases/download/${ARGOCD_VERSION}/argocd-linux-${ARCH}" \
  -o /tmp/argocd
sudo install -m 0755 /tmp/argocd /usr/local/bin/argocd

# ── Trivy ────────────────────────────────────────────────────────────────────
echo "==> Installing Trivy..."
sudo apt-get install -y wget apt-transport-https gnupg
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key \
  | gpg --dearmor | sudo tee /usr/share/keyrings/trivy.gpg > /dev/null
echo "deb [signed-by=/usr/share/keyrings/trivy.gpg] https://aquasecurity.github.io/trivy-repo/deb generic main" \
  | sudo tee /etc/apt/sources.list.d/trivy.list
sudo apt-get update -qq && sudo apt-get install -y trivy

# ── Cosign ───────────────────────────────────────────────────────────────────
echo "==> Installing Cosign..."
COSIGN_VERSION=$(curl -s https://api.github.com/repos/sigstore/cosign/releases/latest \
  | grep '"tag_name"' | cut -d'"' -f4)
curl -fsSL "https://github.com/sigstore/cosign/releases/download/${COSIGN_VERSION}/cosign-linux-${ARCH}" \
  -o /tmp/cosign
sudo install -m 0755 /tmp/cosign /usr/local/bin/cosign

# ── k9s (cluster TUI) ────────────────────────────────────────────────────────
echo "==> Installing k9s..."
K9S_VERSION=$(curl -s https://api.github.com/repos/derailed/k9s/releases/latest \
  | grep '"tag_name"' | cut -d'"' -f4)
curl -fsSL "https://github.com/derailed/k9s/releases/download/${K9S_VERSION}/k9s_Linux_${ARCH}.tar.gz" \
  | tar -xz -C /tmp k9s
sudo install -m 0755 /tmp/k9s /usr/local/bin/k9s

# ── Verify ───────────────────────────────────────────────────────────────────
echo ""
echo "==> Versions installed:"
kubectl version --client --short 2>/dev/null || kubectl version --client
helm version --short
argocd version --client
trivy --version | head -1
cosign version
k9s version --short

echo ""
echo "==> Done. Next: copy ~/.kube/config from Windows or run:"
echo "    export KUBECONFIG=/mnt/c/Users/<you>/.kube/config"
