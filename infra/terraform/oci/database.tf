# Serviço gerenciado "OCI Database with PostgreSQL" (oci_psql_db_system).
#
# IMPORTANTE: este arquivo é um PLACEHOLDER documentado, nunca aplicado nesta
# sessão. Os nomes exatos de argumentos/blocos devem ser conferidos contra a
# versão do provider `oracle/oci` efetivamente usada no momento do deploy
# real (a API deste serviço evoluiu nas últimas versões do provider) — trate
# este arquivo como um rascunho de referência, não como código pronto para
# `terraform apply`.
resource "oci_psql_db_system" "this" {
  compartment_id = var.compartment_ocid
  display_name   = "${local.name_prefix}-db"
  db_version     = "14"
  shape          = "PostgreSQL.VM.Standard.E4.Flex.4.32"

  instance_count               = 1
  instance_ocpu_count          = 2
  instance_memory_size_in_gbs  = 32

  network_details {
    subnet_id = oci_core_subnet.private.id
  }

  credentials {
    username = "meupredio"
    password_details {
      password_type = "PLAIN_TEXT"
      password      = var.db_admin_password
    }
  }

  storage_details {
    system_type            = "OCI_OPTIMIZED_STORAGE"
    is_regionally_durable   = false
    availability_domain     = data.oci_identity_availability_domains.ads.availability_domains[0].name
  }

  freeform_tags = local.common_freeform_tags
}
