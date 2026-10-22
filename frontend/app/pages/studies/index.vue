<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <input v-model="search" type="text" class="input pl-9 w-64 relative" placeholder="Buscar estudio..." @input="debouncedFetch" />
        <select v-model="riskFilter" class="input w-40" @change="fetchPage(1)">
          <option value="">Todos los riesgos</option>
          <option value="BENIGNO">Benigno</option>
          <option value="SOSPECHOSO">Sospechoso</option>
          <option value="MALIGNO">Maligno</option>
        </select>
      </div>
      <NuxtLink to="/studies/new" class="btn-primary">+ Nuevo estudio</NuxtLink>
    </div>

    <div class="card">
      <div class="table-wrapper border-0 rounded-none">
        <table>
          <thead>
            <tr>
              <th>Paciente</th>
              <th>Fecha</th>
              <th>Tipo de lesión</th>
              <th>Localización</th>
              <th>Riesgo</th>
              <th>Estado</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading"><td colspan="7" class="py-10 text-center text-gray-400">Cargando...</td></tr>
            <tr v-else-if="!studies.length"><td colspan="7" class="py-10 text-center text-gray-400">Sin estudios</td></tr>
            <tr v-for="s in studies" :key="s.id">
              <td class="font-medium">{{ s.patient.firstName }} {{ s.patient.lastName }}</td>
              <td>{{ formatDate(s.studyDate) }}</td>
              <td>{{ s.lesionType }}</td>
              <td>{{ s.anatomicLocation }}</td>
              <td><UiBadgeRisk :risk="s.riskLevel" /></td>
              <td>
                <span v-if="s.isProcessed" class="badge bg-emerald-50 text-emerald-700">Procesado</span>
                <span v-else class="badge bg-gray-100 text-gray-500">Pendiente</span>
              </td>
              <td>
                <NuxtLink :to="`/studies/${s.id}`" class="text-brand-600 hover:text-brand-700 text-xs font-medium">Ver →</NuxtLink>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="px-4 border-t border-gray-100">
        <UiPagination :page="meta.page" :pages="meta.pages" :total="meta.total" :limit="meta.limit" @change="fetchPage" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useDebounceFn } from "@vueuse/core";
import { useApiFetch } from "~/composables/useApiFetch";

definePageMeta({ title: "Estudios", middleware: "auth" });

const search     = ref("");
const riskFilter = ref("");
const loading    = ref(false);
const studies    = ref<Record<string, unknown>[]>([]);
const meta       = ref({ page: 1, pages: 1, total: 0, limit: 15 });

const debouncedFetch = useDebounceFn(() => fetchPage(1), 400);

async function fetchPage(page: number) {
  loading.value = true;
  try {
    const res = await useApiFetch<{ data: Record<string, unknown>[]; meta: typeof meta.value }>("/api/studies", {
      query: { page, search: search.value || undefined, riskLevel: riskFilter.value || undefined },
    });
    studies.value = res.data;
    meta.value    = res.meta;
  } finally {
    loading.value = false;
  }
}

function formatDate(d: string) {
  return new Intl.DateTimeFormat("es-MX", { dateStyle: "medium" }).format(new Date(d));
}

onMounted(() => fetchPage(1));
</script>
