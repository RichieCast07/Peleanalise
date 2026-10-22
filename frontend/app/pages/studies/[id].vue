<template>
  <div v-if="pending" class="flex items-center justify-center py-20 text-gray-400">
    Cargando estudio...
  </div>
  <div v-else-if="!study" class="text-center py-20 text-gray-400">
    Estudio no encontrado
  </div>
  <div v-else class="space-y-6">
    <!-- Header -->
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 class="page-title">Estudio Dermatológico</h1>
        <p class="page-subtitle">
          Paciente:
          <NuxtLink :to="`/patients/${study.patient.id}`" class="text-brand-600 font-medium">
            {{ study.patient.firstName }} {{ study.patient.lastName }}
          </NuxtLink>
          · {{ formatDate(study.studyDate) }}
        </p>
      </div>
      <div class="flex flex-wrap items-center gap-3">
        <UiBadgeRisk :risk="study.riskLevel" />
        <button
          v-if="!study.analysis"
          class="btn-primary"
          :disabled="analyzing"
          @click="runAnalysis"
        >
          <svg v-if="analyzing" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
          </svg>
          {{ analyzing ? 'Analizando...' : 'Analizar con IA' }}
        </button>
        <a v-else :href="'/api/reports/' + study.id" target="_blank" class="btn-secondary">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
          </svg>
          Descargar PDF
        </a>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Columna imágenes -->
      <div class="space-y-4">
        <div class="card">
          <div class="card-header">
            <h3 class="font-semibold">Imágenes</h3>
          </div>
          <div class="card-body space-y-4">
            <ImageUploader :study-id="study.id" @uploaded="refresh" />
            <div class="grid grid-cols-2 gap-2">
              <div
                v-for="img in study.images"
                :key="img.id"
                class="relative rounded-lg overflow-hidden aspect-square bg-gray-100"
              >
                <img :src="img.storagePath" class="w-full h-full object-cover" :alt="img.type" />
                <div class="absolute bottom-0 left-0 right-0 bg-black/60 text-white text-[10px] text-center py-1">
                  {{ img.type }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Columna análisis -->
      <div class="lg:col-span-2 space-y-4">
        <template v-if="study.analysis">
          <!-- Predicción IA -->
          <div class="card border-2" :class="predictionBorderClass">
            <div class="card-body">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Predicción IA</p>
                  <p class="text-3xl font-bold" :class="predictionTextClass">
                    {{ study.analysis.prediction?.prediction }}
                  </p>
                  <p class="text-sm text-gray-500 mt-1">
                    Confianza:
                    <strong>{{ predictionPct }}%</strong>
                    · {{ isDemoModel ? 'Modelo de demostración' : 'Modelo v' + study.analysis.prediction?.modelVersion }}
                  </p>
                </div>
                <div :class="['w-14 h-14 rounded-full flex items-center justify-center', predictionIconBg]">
                  <svg class="w-7 h-7" :class="predictionTextClass" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path v-if="riskLevel === 'BENIGNO'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    <path v-else-if="riskLevel === 'SOSPECHOSO'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                    <path v-else-if="riskLevel === 'MALIGNO'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
                  </svg>
                </div>
              </div>
              <div
                v-if="isDemoModel"
                class="mt-4 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800"
              >
                <svg class="w-4 h-4 shrink-0 mt-px" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
                </svg>
                <span>
                  <strong>Resultado de demostración.</strong>
                  No hay un modelo entrenado cargado en el servicio de IA, por lo que estas probabilidades no tienen validez clínica.
                  Las métricas ABCDE sí se calculan sobre la imagen.
                </span>
              </div>
              <div class="mt-4 space-y-2">
                <ProbBar label="Benigno"   :value="study.analysis.prediction?.probBenigno ?? 0"    color="bg-emerald-500" />
                <ProbBar label="Sospechoso" :value="study.analysis.prediction?.probSospechoso ?? 0" color="bg-amber-500" />
                <ProbBar label="Maligno"    :value="study.analysis.prediction?.probMaligno ?? 0"    color="bg-red-500" />
              </div>
            </div>
          </div>

          <!-- ABCDE -->
          <div class="card">
            <div class="card-header">
              <h3 class="font-semibold">Análisis ABCDE</h3>
            </div>
            <div class="card-body">
              <ABCDEMetricsPanel :abcde="study.analysis.abcde" />
            </div>
          </div>
        </template>

        <!-- Sin análisis -->
        <div v-else class="card border-2 border-dashed border-gray-200">
          <div class="card-body py-12 text-center">
            <svg class="w-10 h-10 text-gray-300 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
            </svg>
            <p class="font-medium text-gray-500">Sin análisis de IA</p>
            <p class="text-sm text-gray-400 mt-1">Sube una imagen y ejecuta el análisis</p>
          </div>
        </div>

        <!-- Datos clínicos -->
        <div class="card">
          <div class="card-header">
            <h3 class="font-semibold">Datos clínicos</h3>
          </div>
          <div class="card-body grid grid-cols-2 gap-4 text-sm">
            <div>
              <p class="text-gray-400">Tipo de lesión</p>
              <p class="font-medium">{{ study.lesionType }}</p>
            </div>
            <div>
              <p class="text-gray-400">Localización</p>
              <p class="font-medium">{{ study.anatomicLocation }}</p>
            </div>
            <div class="col-span-2">
              <p class="text-gray-400">Comentarios</p>
              <p class="font-medium">{{ study.clinicalComments ?? '—' }}</p>
            </div>
            <div>
              <p class="text-gray-400">Capturado por</p>
              <p class="font-medium">
                {{ study.capturedBy.firstName }} {{ study.capturedBy.lastName }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useNotification } from '~/composables/useNotification'
import { useApiFetch } from '~/composables/useApiFetch'

definePageMeta({ title: 'Detalle de Estudio', middleware: 'auth' })

const route = useRoute()
const notif = useNotification()
const id    = route.params.id as string

// useApiFetch añade el token Authorization (useFetch a secas recibe 401)
const { data: study, pending, refresh } = await useAsyncData(
  `study-${id}`,
  () => useApiFetch<any>(`/api/studies/${id}`),
  { lazy: true },
)

const analyzing = ref(false)

async function runAnalysis() {
  analyzing.value = true
  try {
    await useApiFetch(`/api/analysis/${id}`, { method: 'POST' })
    await refresh()
    notif.success('Análisis completado', 'El estudio ha sido procesado por la IA')
  } catch (err: unknown) {
    const e = err as { data?: { message?: string } }
    notif.error('Error en el análisis', e?.data?.message)
  } finally {
    analyzing.value = false
  }
}

const riskLevel = computed(() => study.value?.riskLevel ?? '')

// El servicio de IA marca "demo-sin-entrenar" cuando no encuentra el archivo del modelo
const isDemoModel = computed(() =>
  String(study.value?.analysis?.prediction?.modelVersion ?? '').startsWith('demo'),
)

const predictionBorderClass = computed(() => {
  if (riskLevel.value === 'BENIGNO')    return 'border-emerald-200 bg-emerald-50/30'
  if (riskLevel.value === 'SOSPECHOSO') return 'border-amber-200 bg-amber-50/30'
  if (riskLevel.value === 'MALIGNO')    return 'border-red-200 bg-red-50/30'
  return 'border-gray-200'
})

const predictionTextClass = computed(() => {
  if (riskLevel.value === 'BENIGNO')    return 'text-emerald-600'
  if (riskLevel.value === 'SOSPECHOSO') return 'text-amber-600'
  if (riskLevel.value === 'MALIGNO')    return 'text-red-600'
  return 'text-gray-600'
})

const predictionIconBg = computed(() => {
  if (riskLevel.value === 'BENIGNO')    return 'bg-emerald-100'
  if (riskLevel.value === 'SOSPECHOSO') return 'bg-amber-100'
  if (riskLevel.value === 'MALIGNO')    return 'bg-red-100'
  return 'bg-gray-100'
})

const predictionPct = computed(() => {
  const prob = study.value?.analysis?.prediction?.probability ?? 0
  return Math.round(prob * 100)
})

function formatDate(d: string) {
  return new Intl.DateTimeFormat('es-MX', { dateStyle: 'long' }).format(new Date(d))
}
</script>
