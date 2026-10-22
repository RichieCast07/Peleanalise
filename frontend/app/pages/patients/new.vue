<template>
  <div class="text-center py-20 text-gray-400 text-sm">
    <PatientFormModal v-model="open" @saved="onSaved" />
    <p>Registrando nuevo paciente...</p>
  </div>
</template>

<script setup lang="ts">
import type { Patient } from "~/stores/patients";
import { useNotification } from "~/composables/useNotification";

definePageMeta({ title: "Nuevo paciente", middleware: "auth" });

const notif = useNotification();
const open  = ref(true);

function onSaved(p: Patient) {
  notif.success("Paciente guardado correctamente");
  navigateTo(`/patients/${p.id}`);
}

// Al cerrar el modal sin guardar, volvemos a la lista.
watch(open, (v) => { if (!v) navigateTo("/patients"); });
</script>
