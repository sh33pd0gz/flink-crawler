# cert manager
resource "helm_release" "cert_manager" {
  chart            = "cert-manager"
  name             = "cert-manager"
  repository       = "https://charts.jetstack.io"
  version          = "v1.18.2"
  create_namespace = true
  namespace        = "cert-manager"
  cleanup_on_fail  = true
  set = [{
    name  = "installCRDs"
    value = true
  }]
}

# flink
resource "helm_release" "flink" {
  chart            = "flink-kubernetes-operator"
  name             = "flink-kubernetes-operator"
  repository       = "https://downloads.apache.org/flink/flink-kubernetes-operator-1.13.0"
  version          = "v1.13.0"
  create_namespace = true
  namespace        = "flink"
  cleanup_on_fail  = true
  values           = [file("values.yaml")]
  depends_on       = [helm_release.cert_manager]
}


