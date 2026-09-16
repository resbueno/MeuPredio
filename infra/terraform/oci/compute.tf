# Instância única rodando o docker-compose de produção (backend + frontend)
# — adequada para a Fase 1. Escalonamento/alta disponibilidade real ficam
# para uma fase de deploy posterior (fora do escopo deste scaffolding).
data "oci_core_images" "ubuntu" {
  compartment_id           = var.compartment_ocid
  operating_system         = "Canonical Ubuntu"
  operating_system_version = "22.04"
  shape                    = var.compute_shape
  sort_by                  = "TIMECREATED"
  sort_order                = "DESC"
}

resource "oci_core_instance" "app" {
  compartment_id      = var.compartment_ocid
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  display_name        = "${local.name_prefix}-app"
  shape                = var.compute_shape

  shape_config {
    ocpus         = var.compute_ocpus
    memory_in_gbs = var.compute_memory_in_gbs
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.public.id
    assign_public_ip = true
    display_name     = "${local.name_prefix}-app-vnic"
  }

  source_details {
    source_type = "image"
    image_id    = data.oci_core_images.ubuntu.images[0].id
  }

  metadata = {
    ssh_authorized_keys = file(var.ssh_public_key_path)
    # cloud-init real (instalar Docker, clonar o repo, subir o
    # docker-compose de produção) é responsabilidade da fase de deploy —
    # aqui fica só o placeholder documentado.
  }

  freeform_tags = local.common_freeform_tags

  lifecycle {
    ignore_changes = [source_details[0].image_id]
  }
}
