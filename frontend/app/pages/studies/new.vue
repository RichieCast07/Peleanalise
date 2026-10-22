<template>
  <div class="max-w-2xl space-y-6">
    <div>
      <h1 class="page-title">Nuevo estudio</h1>
      <p class="page-subtitle">Registra la lesión y, si quieres, sube la imagen dermatoscópica.</p>
    </div>

    <form class="card" @submit.prevent="submit">
      <div class="card-body grid grid-cols-1 sm:grid-cols-2 gap-4">
        <!-- Paciente -->
        <div class="sm:col-span-2">
          <label class="label">Paciente *</label>
          <input
            v-model="patientSearch"
            class="input"
            placeholder="Buscar por nombre o CURP..."
            @input="debouncedSearch"
          />
          <select v-model="form.patientId" class="input mt-2" required :size="Math.min(Math.max(patients.length, 2), 6)">
            <option v-if="!patients.length" value="" disabled>Sin resultados</option>
            <option v-for="p in patients" :key="p.id" :value="p.id">
              {{ p.firstName }} {{ p.lastName }}{{ p.curp ? ` · ${p.curp}` : "" }}
            </option>
          </select>
          <p class="text-xs text-gray-400 mt-1">
            ¿Paciente nuevo?
            <NuxtLink to="/patients/new" class="text-brand-600 font-medium">Regístralo primero</NuxtLink>
          </p>
        </div>

        <div>
          <label class="label">Tipo de lesión</label>
          <select v-model="form.lesionType" class="input">
            <option v-for="t in lesionTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
          </select>
        </div>
        <div>
          <label class="label">Fecha del estudio</label>
          <input v-model="form.studyDate" type="date" class="input" />
        </div>
        <div class="sm:col-span-2">
          <label class="label">Localización anatómica *</label>
          <input v-model="form.anatomicLocation" class="input" placeholder="Espalda, brazo derecho..." required minlength="2" maxlength="200" />
        </div>
        <div class="sm:col-span-2">
          <label class="label">Comentarios clínicos</label>
          <textarea v-model="form.clinicalComments" class="input h-24 resize-none" maxlength="2000" placeholder="Evolución, síntomas, antecedentes..." />
        </div>
        <div class="sm:col-span-2">
          <label class="label">Imagen (opcional)</label>
          <input type="file" accept="image/jpeg,image/png,image/webp" class="input" @change="onFile" />
          <p class="text-xs text-gray-400 mt-1">JPEG, PNG o WebP · máx. 20 MB</p>
        </div>

        <p v-if="error" class="sm:col-span-2 text-sm text-red-600">{{ error }}</p>
      </div>
      <div class="px-6 py-4 border-t border-gray-100 flex justify-end gap-3">
        <NuxtLink to="/studies" class="btn-secondary">Cancelar</NuxtLink>
        <button class="btn-primary" type="submit" :disabled="saving || !form.patientId">
          {{ saving ? "Guardando..." : "Crear estudio" }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { useDebounceFn } from "@vueuse/core";
import { useNotification } from "~/composables/useNotification";
import { useAuthStore } from "~/stores/auth";
import type { Patient } from "~/stores/patients";

definePageMeta({ title: "Nuevo estudio", middleware: "auth" });

const route  = useRoute();
const notif  = useNotification();
const auth   = useAuthStore();

const lesionTypes = LESION_TYPES;   // app/utils/lesionTypes.ts (compartido con el formulario de edición)

const form = reactive({
  patientId:        (route.query.patientId as string) ?? "",
  lesionType:       "OTRO",
  anatomicLocation: "",
  clinicalComments: "",
  studyDate:        new Date().toISOString().slice(0, 10),
});

const patients      = ref<Patient[]>([]);
const patientSearch = ref("");
const image         = ref<File | null>(null);
const saving        = ref(false);
const error         = ref("");

async function loadPatients() {
  const res = await useApiFetch<{ data: Patient[] }>("/api/patients", {
    query: { limit: 20, search: patientSearch.value || undefined },
  });
  patients.value = res.data;
}
const debouncedSearch = useDebounceFn(loadPatients, 300);

function onFile(e: Event) {
  image.value = (e.target as HTMLInputElement).files?.[0] ?? null;
}

async function submit() {
  error.value = "";
  if (image.value && image.value.size > 20 * 1024 * 1024) {
    error.value = "La imagen supera los 20 MB";
    return;
  }
  saving.value = true;
  try {
    const study = await useApiFetch<{ id: string }>("/api/studies", {
      method: "POST",
      body:   JSON.stringify({
        patientId:        form.patientId,
        lesionType:       form.lesionType,
        anatomicLocation: form.anatomicLocation,
        clinicalComments: form.clinicalComments || undefined,
        studyDate:        form.studyDate || undefined,
      }) as unknown as BodyInit,
    });

    if (image.value) {
      const fd = new FormData();
      fd.append("studyId", study.id);
      fd.append("image", image.value);
      try {
        await $fetch("/api/images/upload", {
          method:  "POST",
          body:    fd,
          headers: { Authorization: `Bearer ${auth.accessToken}` },
        });
      } catch {
        notif.error("El estudio se creó, pero la imagen no se pudo subir");
      }
    }

    notif.success("Estudio creado");
    await navigateTo(`/studies/${study.id}`);
  } catch (err: unknown) {
    console.error("[studies/new]", err);
    const e = err as { data?: { message?: string } };
    error.value = e?.data?.message ?? "No se pudo crear el estudio";
  } finally {
    saving.value = false;
  }
}

onMounted(loadPatients);
</script>
