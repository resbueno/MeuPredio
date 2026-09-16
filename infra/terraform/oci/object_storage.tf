data "oci_objectstorage_namespace" "this" {
  compartment_id = var.compartment_ocid
}

# Bucket para uploads de usuários (ex.: comprovantes, documentos — usado a
# partir da Fase 2 com IA/OCR). Criado já na Fase 1 para fixar a convenção
# de nomes e permissões, mesmo sem consumidores ainda.
resource "oci_objectstorage_bucket" "uploads" {
  compartment_id = var.compartment_ocid
  namespace      = data.oci_objectstorage_namespace.this.namespace
  name           = "${local.name_prefix}-uploads"
  access_type    = "NoPublicAccess"
  versioning     = "Enabled"

  freeform_tags = local.common_freeform_tags
}

# Bucket para backups (ex.: dumps do PostgreSQL).
resource "oci_objectstorage_bucket" "backups" {
  compartment_id = var.compartment_ocid
  namespace      = data.oci_objectstorage_namespace.this.namespace
  name           = "${local.name_prefix}-backups"
  access_type    = "NoPublicAccess"
  versioning     = "Enabled"

  freeform_tags = local.common_freeform_tags
}
