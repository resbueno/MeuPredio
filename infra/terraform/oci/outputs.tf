output "app_instance_public_ip" {
  description = "IP publico da instancia de aplicacao (backend+frontend via docker-compose)."
  value       = oci_core_instance.app.public_ip
}

output "vcn_id" {
  description = "OCID da VCN criada."
  value       = oci_core_vcn.this.id
}

output "db_system_id" {
  description = "OCID do banco gerenciado."
  value       = oci_psql_db_system.this.id
}

output "uploads_bucket_name" {
  description = "Nome do bucket de uploads."
  value       = oci_objectstorage_bucket.uploads.name
}

output "backups_bucket_name" {
  description = "Nome do bucket de backups."
  value       = oci_objectstorage_bucket.backups.name
}
