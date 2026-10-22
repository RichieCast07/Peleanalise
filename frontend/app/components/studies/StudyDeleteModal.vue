<template>
  <UiModal
    :model-value="modelValue"
    title="Eliminar estudio"
    size="sm"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <p class="text-sm text-gray-600">
      ¿Eliminar el estudio de <strong>{{ patientName || "este paciente" }}</strong><span v-if="studyDate"> del {{ studyDate }}</span>?
    </p>
    <p class="text-xs text-gray-400 mt-2">
      Dejará de mostrarse en la aplicación. El registro se conserva en la base de datos para auditoría.
    </p>
    <p v-if="error" class="text-sm text-red-600 mt-3">{{ error }}</p>
    <template #footer>
      <button type="button" class="btn-secondary" :disabled="deleting" @click="$emit('update:modelValue', false)">Cancelar</button>
      <button type="button" class="btn-danger" :disabled="deleting" @click="confirm">
        {{ deleting ? "Eliminando..." : "Eliminar" }}
      </button>
    </template>
  </UiModal>
</template>

<script setup lang="ts">
import { useApiFetch } from "~/composables/useApiFetch";
import { useNotification } from "~/composables/useNotification";

const props = defineProps<{
  modelValue:   boolean;
  studyId:      string;
  patientName?: string;
  studyDate?:   string;
}>();
const emit = defineEmits<{ (e: "update:modelValue", v: boolean): void; (e: "deleted"): void }>();

const notif    = useNotification();
const deleting = ref(false);
const error    = ref("");

watch(() => props.modelValue, (open) => { if (open) error.value = ""; });

async function confirm() {
  deleting.value = true;
  error.value    = "";
  try {
    await useApiFetch(`/api/studies/${props.studyId}`, { method: "DELETE" });
    notif.success("Estudio eliminado");
    emit("update:modelValue", false);
    emit("deleted");
  } catch (err: unknown) {
    const e = err as { data?: { message?: string } };
    error.value = e?.data?.message ?? "No se pudo eliminar el estudio";
  } finally {
    deleting.value = false;
  }
}
</script>
