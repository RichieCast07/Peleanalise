// Tipos de lesión (deben coincidir con el enum LesionType de prisma/schema.prisma)
export const LESION_TYPES = [
  { value: "OTRO",                    label: "Otro / sin definir" },
  { value: "MELANOMA",                label: "Melanoma" },
  { value: "NEVUS",                   label: "Nevus" },
  { value: "CARCINOMA_BASOCELULAR",   label: "Carcinoma basocelular" },
  { value: "CARCINOMA_ESPINOCELULAR", label: "Carcinoma espinocelular" },
  { value: "QUERATOSIS_ACTINCA",      label: "Queratosis actínica" },
  { value: "DERMATOFIBROMA",          label: "Dermatofibroma" },
  { value: "LESION_VASCULAR",         label: "Lesión vascular" },
] as const;

export function lesionLabel(value: string): string {
  return LESION_TYPES.find((t) => t.value === value)?.label ?? value;
}
