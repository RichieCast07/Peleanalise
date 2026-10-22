<template>
  <div class="space-y-4">
    <div class="toolbar">
      <div class="toolbar-group">
        <input v-model="search" type="text" class="input sm:w-64" placeholder="Buscar estudio..." @input="debouncedFetch" />
        <select v-model="riskFilter" class="input sm:w-44" @change="fetchPage(1)">
          <option value="">Todos los riesgos</option>
          <option value="BENIGNO">Benigno</option>
          <option value="SOSPECHOSO">Sospechoso</option>
          <option value="MALIGNO">Maligno</option>
        </select>
      </div>
      <NuxtLink to="/studies/new" class="btn-primary whitespace-nowrap">+ Nuevo estudio</NuxtLink>
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
                <div class="flex items-center justify-end gap-3">
                  <NuxtLink :to="`/studies/${s.id}`" class="text-brand-600 hover:text-brand-700 text-xs font-medium">Ver →</NuxtLink>
                  <button
                    v-if="can('studies:edit')"
                    type="button"
                    class="text-xs font-medium text-gray-500 hover:text-gray-800"
                    @click="askEdit(s)"
                  >Editar</button>
                  <button
                    v-if="can('studies:delete')"
                    type="button"
                    class="text-xs font-medium text-red-500 hover:text-red-700"
                    @click="askDelete(s)"
                  >Eliminar</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="px-4 border-t border-gray-100">
        <UiPagination :page="meta.page" :pages="meta.pages" :total="meta.total" :limit="meta.limit" @change="fetchPage" />
      </div>
    </div>

    <StudyEditModal v-model="editOpen" :study="toEdit" @saved="fetchPage(meta.page)" />

    <StudyDeleteModal
      v-model="deleteOpen"
      :study-id="toDelete?.id ?? ''"
      :patient-name="toDelete ? `${toDelete.patient.firstName} ${toDelete.patient.lastName}` : ''"
      :study-date="toDelete ? formatDate(toDelete.studyDate) : ''"
      @deleted="onDeleted"
    />
  </div>
</template>

<script setup lang="ts">
import { useDebounceFn } from "@vueuse/core";
import { useApiFetch } from "~/composables/useApiFetch";
import { useRBAC } from "~/composables/useRBAC";

definePageMeta({ title: "Estudios", middleware: "auth" });

const { can } = useRBAC();

const editOpen = ref(false);
const toEdit   = ref<any>(null);

function askEdit(s: any) {
  toEdit.value  = s;
  editOpen.value = true;
}

const deleteOpen = ref(false);
const toDelete   = ref<any>(null);

function askDelete(s: any) {
  toDelete.value  = s;
  deleteOpen.value = true;
}

async function onDeleted() {
  // Si era el único estudio de la última página, retrocede una página
  const lastPageNowEmpty = studies.value.length === 1 && meta.value.page > 1;
  await fetchPage(lastPageNowEmpty ? meta.value.page - 1 : meta.value.page);
}

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
