import { Download } from "lucide-react";

import { Button } from "@/components/ui/button";
import { LiveScanCard } from "@/components/dashboard/live-scan-card";
import { ProspectsTable } from "@/components/dashboard/prospects-table";
import { RadarStatsCards } from "@/components/dashboard/radar-stats-cards";
import { getLeadsExportUrl } from "@/lib/api-client";

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      <div className="animate-fade-in border-b border-border pb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="page-title">ProspectsRadar</h1>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20">
              Agency Edition
            </span>
          </div>
          <p className="text-sm text-muted-foreground mt-1.5 max-w-2xl">
            Leads e-commerce pré-qualifiés sur leur visibilité IA — avec preuve de douleur chiffrée (score 0-100) et angle de cold email déjà écrit.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button asChild size="sm" variant="outline" className="h-8 text-xs gap-1.5">
            <a href={getLeadsExportUrl("all")} download>
              <Download className="h-3.5 w-3.5" />
              Export Global CSV
            </a>
          </Button>
        </div>
      </div>

      <RadarStatsCards />

      <div className="grid gap-6 xl:grid-cols-3">
        <div className="xl:col-span-2 space-y-6">
          <ProspectsTable />
        </div>
        <div className="space-y-6">
          <LiveScanCard />
        </div>
      </div>
    </div>
  );
}
