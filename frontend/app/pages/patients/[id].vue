<template>
  <div v-if="pending" class="flex items-center justify-center py-20 text-gray-400">Cargando paciente...</div>
  <div v-else-if="!patient" class="text-center py-20 text-gray-400">Paciente no encontrado</div>
  <div v-else class="space-y-6">
    <!-- Header -->
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 class="page-title">{{ patient.firstName }} {{ patient.lastName }}</h1>
        <p class="page-subtitle capitalize">
          {{ patient.sex.toLowerCase() }} · {{ age }} años · Registrado el {{ formatDate(patient.createdAt) }}
        </p>
      </div>
      <div class="flex items-center gap-3">
        <button class="btn-secondary" @click="editing = true">Editar</button>
        <NuxtLink :to="`/studies/new?patientId=${patient.id}`" class="btn-primary">+ Nuevo estudio</NuxtLink>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Datos personales -->
      <div class="card">
        <div class="card-header"><h3 class="font-semibold">Datos del paciente</h3></div>
        <div class="card-body space-y-3 text-sm">
          <div><p class="text-gray-400">Fecha de nacimiento</p><p class="font-medium">{{ formatDate(patient.birthDate) }}</p></div>
          <div><p class="text-gray-400">CURP</p><p class="font-medium font-mono">{{ patient.curp ?? "—" }}</p></div>
          <div><p class="text-gray-400">Teléfono</p><p class="font-medium">{{ patient.phone ?? "—" }}</p></div>
          <div><p class="text-gray-400">Correo</p><p class="font-medium">{{ patient.email ?? "—" }}</p></div>
          <div><p class="text-gray-400">Dirección</p><p class="font-medium">{{ patient.address ?? "—" }}</p></div>
          <div><p class="text-gray-400">Observaciones</p><p class="font-medium">{{ patient.observations ?? "—" }}</p></div>
        </div>
      </div>

      <!-- Estudios -->
      <div class="lg:col-span-2 space-y-6">
        <div class="card">
          <div class="card-header"><h3 class="font-semibold">Estudios ({{ patient.studies.length }})</h3></div>
          <div class="table-wrapper border-0 rounded-none">
            <table>
              <thead>
                <tr><th>Fecha</th><th>Tipo de lesión</th><th>Localización</th><th>Riesgo</th><th></th></tr>
              </thead>
              <tbody>
                <tr v-if="!patient.studies.length">
                  <td colspan="5" class="py-8 text-center text-gray-400">Sin estudios registrados</td>
                </tr>
                <tr v-for="s in patient.studies" :key="s.id">
                  <td>{{ formatDate(s.studyDate) }}</td>
                  <td>{{ s.lesionType }}</td>
                  <td>{{ s.anatomicLocation }}</td>
                  <td><UiBadgeRisk :risk="s.riskLevel" /></td>
                  <td><NuxtLink :to="`/studies/${s.id}`" class="text-brand-600 hover:text-brand-700 text-xs font-medium">Ver →</NuxtLink></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="card">
          <div class="card-header"><h3 class="font-semibold">Expediente clínico</h3></div>
          <div class="card-body space-y-3 text-sm">
            <p v-if="!patient.medicalRecords.length" class="text-gray-400">Sin consultas registradas</p>
            <div v-for="r in patient.medicalRecords" :key="r.id" class="border border-gray-100 rounded-lg p-3">
              <p class="font-medium">{{ r.consultationReason }}</p>
              <p class="text-xs text-gray-400">
                {{ formatDate(r.consultationDate) }} · Dr(a). {{ r.doctor.firstName }} {{ r.doctor.lastName }}
              </p>
              <p v-if="r.preliminaryDiagnosis" class="mt-1 text-gray-600">{{ r.preliminaryDiagnosis }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <PatientFormModal v-model="editing" :patient="patient" @saved="onSaved" />
  </div>
</template>

<script setup lang="ts">
import { useNotification } from "~/composables/useNotification";

definePageMeta({ title: "Detalle de Paciente", middleware: "auth" });

const route   = useRoute();
const notif   = useNotification();
const id      = route.params.id as string;
const editing = ref(false);

const { data: patient, pending, refresh } = await useAsyncData(
  `patient-${id}`,
  () => useApiFetch<any>(`/api/patients/${id}`),
  { lazy: true },
);

const age = computed(() => {
  if (!patient.value) return "";
  const b = new Date(patient.value.birthDate);
  const n = new Date();
  let a = n.getFullYear() - b.getFullYear();
  if (n < new Date(n.getFullYear(), b.getMonth(), b.getDate())) a--;
  return a;
});

async function onSaved() {
  editing.value = false;
  await refresh();
  notif.success("Paciente actualizado");
}

function formatDate(d: string) {
  return new Intl.DateTimeFormat("es-MX", { dateStyle: "medium", timeZone: "UTC" }).format(new Date(d));
}
</script>
