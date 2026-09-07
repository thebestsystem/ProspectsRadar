"use client";

import { useState } from "react";
import {
  AlertCircle,
  ArrowRight,
  Globe,
  Loader2,
  Radar,
  ShieldAlert,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { useScanTarget } from "@/lib/queries";
import type { AuditResult } from "@ai-saas-starter-kit/shared";

export function LiveScanCard() {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState<AuditResult | null>(null);

  const scanMutation = useScanTarget();

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    try {
      const data = await scanMutation.mutateAsync({ url: url.trim() });
      setResult(data);
    } catch {
      // Error handled by mutation state
    }
  };

  return (
    <Card className="border-border/70 bg-card/60 backdrop-blur-sm shadow-sm animate-fade-in-up stagger-4">
      <CardHeader className="p-5 pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-bold tracking-tight text-foreground flex items-center gap-2">
            <Radar className="h-4 w-4 text-primary" />
            Scanner Instantané de Démonstration
          </CardTitle>
          <Badge variant="outline" className="text-[10px] uppercase font-semibold text-primary border-primary/30">
            5 Piliers Déterministes
          </Badge>
        </div>
        <CardDescription className="text-xs text-muted-foreground mt-1">
          Testez l&apos;invisibilité IA de n&apos;importe quelle boutique e-commerce en direct.
        </CardDescription>
      </CardHeader>

      <CardContent className="p-5 pt-2 space-y-4">
        <form onSubmit={handleScan} className="flex gap-2">
          <div className="relative flex-1">
            <Globe className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="ex: respire.co, horace.co ou monsite.fr"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="pl-8 h-9 text-xs"
              disabled={scanMutation.isPending}
            />
          </div>
          <Button
            type="submit"
            size="sm"
            disabled={scanMutation.isPending || !url.trim()}
            className="h-9 px-4 text-xs font-semibold gap-1.5"
          >
            {scanMutation.isPending ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                Audit en cours...
              </>
            ) : (
              <>
                Auditer
                <ArrowRight className="h-3.5 w-3.5" />
              </>
            )}
          </Button>
        </form>

        {scanMutation.isError && (
          <div className="rounded-md bg-destructive/10 border border-destructive/20 p-3 text-xs text-destructive flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{scanMutation.error?.message || "Impossible de scanner ce domaine."}</span>
          </div>
        )}

        {result && (
          <div className="rounded-lg border border-border/60 bg-muted/20 p-4 space-y-4 animate-fade-in">
            <div className="flex items-center justify-between pb-2 border-b border-border/40">
              <div>
                <h4 className="text-sm font-bold text-foreground">{result.domain}</h4>
                <p className="text-[11px] text-muted-foreground">{result.name}</p>
              </div>
              <div className="text-right">
                <span className="text-xl font-extrabold text-foreground">
                  {result.score}
                  <span className="text-xs text-muted-foreground font-normal">/100</span>
                </span>
                <p className="text-[10px] font-semibold text-rose-500">
                  {result.statusLabel}
                </p>
              </div>
            </div>

            <div className="space-y-2.5">
              <span className="text-xs font-semibold text-muted-foreground">Piliers d&apos;Évaluation IA :</span>
              {Object.entries(result.pillars).map(([key, pillar]) => (
                <div key={key} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">{pillar.label} ({pillar.weight})</span>
                    <span className="font-semibold text-foreground">{pillar.score}/100</span>
                  </div>
                  <Progress value={pillar.score} className="h-1.5" />
                </div>
              ))}
            </div>

            {result.brokenItems.length > 0 && (
              <div className="space-y-1.5 pt-2">
                <span className="text-xs font-semibold text-foreground flex items-center gap-1">
                  <ShieldAlert className="h-3.5 w-3.5 text-rose-500" />
                  Failles Détectées ({result.brokenItems.length}) :
                </span>
                <div className="space-y-1">
                  {result.brokenItems.slice(0, 3).map((item, idx) => (
                    <div
                      key={idx}
                      className="text-[11px] rounded bg-background/80 p-2 border border-border/40"
                    >
                      <span className="font-semibold text-foreground block">{item.title}</span>
                      <span className="text-muted-foreground">{item.impact}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
