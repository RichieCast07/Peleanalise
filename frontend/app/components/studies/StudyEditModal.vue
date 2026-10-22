<template>
  <UiModal
    :model-value="modelValue"
    title="Editar estudio"
    size="lg"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <form class="grid grid-cols-1 sm:grid-cols-2 gap-4" @submit.prevent="save">
      <div class="sm:col-span-2">
        <p class="text-xs text-gray-400">Paciente</p>
        <p class="text-sm font-medium text-gray-800">{{ patientName }}</p>
      </div>
      <div>
        <label class="label">Tipo de lesión</label>
        <select v-model="form.lesionType" class="input">
          <option v-for="t in LESION_TYPES" :key="t.value" :value="t.value">{{ t.label }}</option>
        </select>
      </div>
      <div>
        <label class="label">Fecha del estudio</label>
        <input v-model="form.studyDate" type="date" class="input" required />
      </div>
      <div class="sm:col-span-2">
        <label class="label">Localización anatómica *</label>
        <input v-model="form.anatomicLocation" class="input" required minlength="2" maxlength="200" placeholder="Espalda, brazo derecho..." />
      </div>
      <div class="sm:col-span-2">
        <label class="label">Comentarios clínicos</label>
        <textarea v-model="form.clinicalComments" class="input h-28 resize-none" maxlength="2000" placeholder="Evolución, síntomas, antecedentes..." />
      </div>
      <p v-if="error" class="sm:col-span-2 text-sm text-red-600">{{ error }}</p>
    </form>
    <template #footer>
      <button type="button" class="btn-secondary" :disabled="saving" @click="$emit('update:modelValue', false)">Cancelar</button>
      <button type="button" class="btn-primary" :disabled="saving" @click="save">
        {{ saving ? "Guardando..." : "Guardar cambios" }}
      </button>
    </template>
  </UiModal>
</template>

<script setup lang="ts">
import { useApiFetch } from "~/composables/useApiFetch";
import { useNotification } from "~/composables/useNotification";

const props = defineProps<{
  modelValue: boolean;
  study:      Record<string, any> | null;
}>();
const emit = defineEmits<{ (e: "update:modelValue", v: boolean): void; (e: "saved"): void }>();

const notif  = useNotification();
const saving = ref(false);
const error  = ref("");

const form = reactive({
  lesionType:       "OTRO",
  anatomicLocation: "",
  clinicalComments: "",
  studyDate:        "",
});

const patientName = computed(() =>
  props.study?.patient ? `${props.study.patient.firstName} ${props.study.patient.lastName}` : "",
);

// Cada vez que se abre, se cargan los datos actuales del estudio
watch(
  () => props.modelValue,
  (open) => {
    if (!open || !props.study) return;
    error.value = "";
    form.lesionType       = props.study.lesionType ?? "OTRO";
    form.anatomicLocation = props.study.anatomicLocation ?? "";
    form.clinicalComments = props.study.clinicalComments ?? "";
    form.studyDate        = String(props.study.studyDate ?? "").slice(0, 10);
  },
);

async function save() {
  if (!props.study) return;
  if (form.anatomicLocation.trim().length < 2) {
    error.value = "La localización debe tener al menos 2 caracteres";
    return;
  }
  saving.value = true;
  error.value  = "";
  try {
    await useApiFetch(`/api/studies/${props.study.id}`, {
      method: "PUT",
      body: JSON.stringify({
        lesionType:       form.lesionType,
        anatomicLocation: form.anatomicLocation.trim(),
        clinicalComments: form.clinicalComments,
        studyDate:        form.studyDate,
      }) as unknown as BodyInit,
    });
    notif.success("Estudio actualizado");
    emit("update:modelValue", false);
    emit("saved");
  } catch (err: unknown) {
    const e = err as { data?: { message?: string } };
    error.value = e?.data?.message ?? "No se pudo guardar el estudio";
  } finally {
    saving.value = false;
  }
}
</script>
