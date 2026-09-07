"use client";

import type { ReactNode } from "react";
import { AlertOctagon, Flame, Radar, ShieldAlert, Users } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useLeadsStats } from "@/lib/queries";

function StatCard({
  title,
  icon: Icon,
  loading,
  error,
  children,
  stagger,
}: {
  title: string;
  icon: typeof Radar;
  loading: boolean;
  error?: boolean;
  children: ReactNode;
  stagger: number;
}) {
  return (
    <Card className={`card-hover animate-fade-in-up stagger-${stagger} border-border/70 bg-card/60 backdrop-blur-sm`}>
      <CardHeader className="flex flex-row items-center justify-between pt-4 pb-2 px-4 space-y-0">
        <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          {title}
        </CardTitle>
        <div className="stat-icon-wrap rounded-lg bg-primary/10 p-2 text-primary">
          <Icon className="h-4 w-4" />
        </div>
      </CardHeader>
      <CardContent className="pb-5 px-4">
        {loading ? (
          <Skeleton className="h-8 w-24" />
        ) : error ? (
          <span className="stat-value text-muted-foreground">—</span>
        ) : (
          children
        )}
      </CardContent>
    </Card>
  );
}

export function RadarStatsCards() {
  const { data: stats, isLoading, isError } = useLeadsStats();

  const topFlaw = stats?.top_failing_pillars
    ? Object.keys(stats.top_failing_pillars)[0] ?? "Schema.org manquant"
    : "Schema.org manquant";

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <StatCard
        title="Leads Qualifiés"
        icon={Users}
        loading={isLoading}
        error={isError}
        stagger={1}
      >
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold tracking-tight text-foreground">
            {stats?.total_leads ?? 0}
          </span>
          <span className="text-xs text-muted-foreground font-medium">prêts à prospecter</span>
        </div>
        <p className="text-[11px] text-muted-foreground mt-1">
          Boutiques e-commerce avec douleur chiffrée
        </p>
      </StatCard>

      <StatCard
        title="Taux de Douleur Forte"
        icon={Flame}
        loading={isLoading}
        error={isError}
        stagger={2}
      >
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold tracking-tight text-rose-500">
            {stats?.critical_pain_rate ?? 0}%
          </span>
          <span className="text-xs text-rose-500/80 font-medium">Score &lt; 40</span>
        </div>
        <p className="text-[11px] text-muted-foreground mt-1">
          Invisibles sur ChatGPT Search &amp; Perplexity
        </p>
      </StatCard>

      <StatCard
        title="Score Moyen du Marché"
        icon={ShieldAlert}
        loading={isLoading}
        error={isError}
        stagger={3}
      >
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold tracking-tight text-amber-500">
            {stats?.average_score ?? 0}/100
          </span>
          <span className="text-xs text-amber-500/80 font-medium">Vulnérabilité élevée</span>
        </div>
        <p className="text-[11px] text-muted-foreground mt-1">
          Moyenne des 5 piliers de visibilité IA
        </p>
      </StatCard>

      <StatCard
        title="Faille N°1 Détectée"
        icon={AlertOctagon}
        loading={isLoading}
        error={isError}
        stagger={4}
      >
        <div className="truncate text-base font-bold tracking-tight text-foreground" title={topFlaw}>
          {topFlaw}
        </div>
        <p className="text-[11px] text-muted-foreground mt-1 truncate">
          Angle d&apos;accroche commercial prioritaire
        </p>
      </StatCard>
    </div>
  );
}
