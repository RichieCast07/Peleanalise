<template>
  <UiModal :model-value="modelValue" :title="patient ? 'Editar paciente' : 'Nuevo paciente'" size="lg" @update:model-value="$emit('update:modelValue', $event)">
    <form @submit.prevent="submit" class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div>
        <label class="label">Nombre(s) *</label>
        <input v-model="form.firstName" class="input" :class="{ 'input-error': errors.firstName }" placeholder="María" required />
        <p v-if="errors.firstName" class="field-error">{{ errors.firstName }}</p>
      </div>
      <div>
        <label class="label">Apellidos *</label>
        <input v-model="form.lastName" class="input" placeholder="González López" required />
      </div>
      <div>
        <label class="label">Sexo *</label>
        <select v-model="form.sex" class="input" required>
          <option value="">Seleccionar...</option>
          <option value="MASCULINO">Masculino</option>
          <option value="FEMENINO">Femenino</option>
          <option value="OTRO">Otro</option>
        </select>
      </div>
      <div>
        <label class="label">Fecha de nacimiento *</label>
        <input v-model="form.birthDate" type="date" class="input" required />
      </div>
      <div>
        <label class="label">CURP</label>
        <input v-model="form.curp" class="input font-mono text-sm" placeholder="GOML890101HDFNZS03" maxlength="18" />
      </div>
      <div>
        <label class="label">Teléfono</label>
        <input v-model="form.phone" type="tel" class="input" placeholder="55 1234 5678" />
      </div>
      <div>
        <label class="label">Correo electrónico</label>
        <input v-model="form.email" type="email" class="input" placeholder="paciente@correo.mx" />
      </div>
      <div class="sm:col-span-2">
        <label class="label">Dirección</label>
        <input v-model="form.address" class="input" placeholder="Calle, colonia, ciudad, CP" />
      </div>
      <div class="sm:col-span-2">
        <label class="label">Observaciones</label>
        <textarea v-model="form.observations" class="input h-20 resize-none" placeholder="Antecedentes, alergias, notas..." />
      </div>
    </form>
    <template #footer>
      <button class="btn-secondary" @click="$emit('update:modelValue', false)">Cancelar</button>
      <button class="btn-primary" :disabled="saving" @click="submit">
        {{ saving ? "Guardando..." : (patient ? "Actualizar" : "Crear paciente") }}
      </button>
    </template>
  </UiModal>
</template>

<script setup lang="ts">
import { usePatientsStore, type Patient } from "~/stores/patients";

const props = defineProps<{ modelValue: boolean; patient?: Patient | null }>();
const emit  = defineEmits(["update:modelValue", "saved"]);

const store  = usePatientsStore();
const saving = ref(false);
const errors = reactive<Record<string, string>>({});

const form = reactive({
  firstName:    "",
  lastName:     "",
  sex:          "",
  birthDate:    "",
  curp:         "",
  phone:        "",
  email:        "",
  address:      "",
  observations: "",
});

function resetForm() {
  Object.keys(form).forEach((k) => ((form as Record<string, string>)[k] = ""));
  Object.keys(errors).forEach((k) => delete errors[k]);
}

function fillForm(p: Patient) {
  Object.keys(errors).forEach((k) => delete errors[k]);
  Object.assign(form, {
    firstName:    p.firstName,
    lastName:     p.lastName,
    sex:          p.sex,
    birthDate:    p.birthDate?.slice(0, 10) ?? "",
    curp:         p.curp ?? "",
    phone:        p.phone ?? "",
    email:        p.email ?? "",
    address:      p.address ?? "",
    observations: p.observations ?? "",
  });
}

// El componente sigue montado entre una apertura y otra, así que el formulario se (re)inicia
// CADA VEZ que se abre: con los datos del paciente al editar, o vacío al crear. Antes solo se
// reiniciaba cuando cambiaba `patient`, y al crear otro (patient = null) quedaban los datos anteriores.
watch(
  () => props.modelValue,
  (open) => {
    if (!open) return;
    if (props.patient) fillForm(props.patient);
    else resetForm();
  },
  { immediate: true },
);

async function submit() {
  if (!form.firstName || !form.lastName || !form.sex || !form.birthDate) {
    errors.firstName = !form.firstName ? "Requerido" : "";
    return;
  }
  saving.value = true;
  try {
    const saved = props.patient
      ? await store.update(props.patient.id, form)
      : await store.create(form as Parameters<typeof store.create>[0]);
    emit("saved", saved);
  } catch (err: unknown) {
    const e = err as { data?: { message?: string } };
    errors.firstName = e?.data?.message ?? "Error al guardar";
  } finally {
    saving.value = false;
  }
}
</script>
