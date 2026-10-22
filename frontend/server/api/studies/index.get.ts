import { z } from "zod";
import { prisma } from "../../utils/prisma";

const querySchema = z.object({
  page:        z.coerce.number().min(1).default(1),
  limit:       z.coerce.number().min(1).max(100).default(15),
  patientId:   z.string().uuid().optional(),
  riskLevel:   z.enum(["BENIGNO", "SOSPECHOSO", "MALIGNO"]).optional(),
  isProcessed: z.coerce.boolean().optional(),
  search:      z.string().optional(),
});

export default defineEventHandler(async (event) => {
  const q    = await getValidatedQuery(event, querySchema.parse);
  const skip = (q.page - 1) * q.limit;

  const where: Record<string, unknown> = { deletedAt: null };
  if (q.patientId)            where.patientId   = q.patientId;
  if (q.riskLevel)            where.riskLevel   = q.riskLevel;
  if (q.isProcessed !== undefined) where.isProcessed = q.isProcessed;
  if (q.search) {
    where.OR = [
      { anatomicLocation: { contains: q.search } },
      { clinicalComments: { contains: q.search } },
      { patient: { firstName: { contains: q.search } } },
      { patient: { lastName:  { contains: q.search } } },
    ];
  }

  const [studies, total] = await Promise.all([
    prisma.study.findMany({
      where,
      include: {
        patient:   { select: { id: true, firstName: true, lastName: true } },
        capturedBy: { select: { firstName: true, lastName: true } },
        images:    { where: { type: "ORIGINAL" }, take: 1 },
        analysis:  { include: { prediction: true } },
      },
      orderBy: { studyDate: "desc" },
      skip,
      take: q.limit,
    }),
    prisma.study.count({ where }),
  ]);

  return {
    data: studies,
    meta: { total, page: q.page, limit: q.limit, pages: Math.ceil(total / q.limit) },
  };
});
