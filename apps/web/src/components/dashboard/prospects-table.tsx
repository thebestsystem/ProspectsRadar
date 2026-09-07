"use client";

import { useState } from "react";
import {
  Check,
  Copy,
  Download,
  ExternalLink,
  FileText,
  Mail,
  Search,
  Sparkles,
  UserCheck,
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { getLeadPdfUrl, getLeadsExportUrl } from "@/lib/api-client";
import { useLeads } from "@/lib/queries";
import type { ProspectLead } from "@ai-saas-starter-kit/shared";

export function ProspectsTable() {
  const [vertical, setVertical] = useState("all");
  const [search, setSearch] = useState("");
  const [selectedLead, setSelectedLead] = useState<ProspectLead | null>(null);
  const [copied, setCopied] = useState(false);

  const { data: leads, isLoading, isError } = useLeads(vertical);

  const filteredLeads = (leads ?? []).filter((lead) => {
    const q = search.toLowerCase().trim();
    if (!q) return true;
    return (
      lead.domain.toLowerCase().includes(q) ||
      lead.company_name.toLowerCase().includes(q) ||
      lead.decision_maker.name.toLowerCase().includes(q) ||
      lead.decision_maker.email.toLowerCase().includes(q)
    );
  });

  const handleCopyPitch = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      // Clipboard fallback
    }
  };

  return (
    <>
      <Card className="border-border/70 bg-card/60 backdrop-blur-sm shadow-sm animate-fade-in-up stagger-3">
        <CardHeader className="p-5 pb-4 border-b border-border/50">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <CardTitle className="text-lg font-bold tracking-tight text-foreground flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-primary" />
                Pipeline de Leads E-commerce Qualifiés
              </CardTitle>
              <CardDescription className="text-xs text-muted-foreground mt-1">
                Leads scannés avec score de douleur IA, décideur enrichi et angle de cold email rédigé.
              </CardDescription>
            </div>

            <div className="flex flex-wrap items-center gap-2.5">
              <div className="relative w-full sm:w-60">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Filtrer par boutique ou nom..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-8 h-9 text-xs"
                />
              </div>

              <Select value={vertical} onValueChange={setVertical}>
                <SelectTrigger className="w-[170px] h-9 text-xs">
                  <SelectValue placeholder="Verticale" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tous les secteurs</SelectItem>
                  <SelectItem value="shopify_fr">Shopify France (DTC)</SelectItem>
                  <SelectItem value="mode_beaute">Mode &amp; Beauté</SelectItem>
                  <SelectItem value="maison_deco">Maison &amp; Décoration</SelectItem>
                </SelectContent>
              </Select>

              <Button asChild size="sm" variant="outline" className="h-9 gap-1.5 text-xs">
                <a href={getLeadsExportUrl(vertical)} download>
                  <Download className="h-3.5 w-3.5" />
                  Exporter CSV
                </a>
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent border-border/50 bg-muted/20">
                  <TableHead className="w-[200px] text-xs font-semibold">Boutique &amp; Domaine</TableHead>
                  <TableHead className="text-xs font-semibold">Score IA</TableHead>
                  <TableHead className="text-xs font-semibold">Failles Critiques</TableHead>
                  <TableHead className="text-xs font-semibold">Décideur Identifié</TableHead>
                  <TableHead className="text-right text-xs font-semibold pr-4">Actions de Prospection</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <TableRow key={i}>
                      <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                      <TableCell><Skeleton className="h-6 w-16" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-44" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-28" /></TableCell>
                      <TableCell><Skeleton className="h-8 w-24 ml-auto" /></TableCell>
                    </TableRow>
                  ))
                ) : isError ? (
                  <TableRow>
                    <TableCell colSpan={5} className="h-32 text-center text-sm text-destructive">
                      Impossible de charger les leads de prospection.
                    </TableCell>
                  </TableRow>
                ) : filteredLeads.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="h-32 text-center text-sm text-muted-foreground">
                      Aucun lead correspondant dans ce secteur.
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredLeads.map((lead) => (
                    <TableRow key={lead.id} className="border-border/40 hover:bg-muted/30 transition-colors">
                      <TableCell className="font-medium">
                        <div className="flex flex-col">
                          <span className="text-sm font-semibold text-foreground">
                            {lead.company_name}
                          </span>
                          <a
                            href={`https://${lead.domain}`}
                            target="_blank"
                            rel="noreferrer"
                            className="text-xs text-muted-foreground hover:text-primary flex items-center gap-1 transition-colors"
                          >
                            {lead.domain}
                            <ExternalLink className="h-2.5 w-2.5 opacity-60" />
                          </a>
                        </div>
                      </TableCell>

                      <TableCell>
                        <Badge
                          variant="outline"
                          className={
                            lead.score < 40
                              ? "border-rose-500/30 bg-rose-500/10 text-rose-500 font-bold"
                              : lead.score < 60
                              ? "border-amber-500/30 bg-amber-500/10 text-amber-500 font-bold"
                              : "border-emerald-500/30 bg-emerald-500/10 text-emerald-500 font-bold"
                          }
                        >
                          {lead.score}/100
                        </Badge>
                      </TableCell>

                      <TableCell>
                        <div className="flex flex-wrap gap-1 max-w-[280px]">
                          {lead.failing_pillars.slice(0, 2).map((pillar, idx) => (
                            <span
                              key={idx}
                              className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground border border-border/50 truncate"
                            >
                              {pillar}
                            </span>
                          ))}
                          {lead.broken_items.length > 2 && (
                            <span className="text-[10px] text-muted-foreground self-center">
                              +{lead.broken_items.length - 2}
                            </span>
                          )}
                        </div>
                      </TableCell>

                      <TableCell>
                        <div className="flex flex-col text-xs">
                          <span className="font-medium text-foreground flex items-center gap-1">
                            <UserCheck className="h-3 w-3 text-emerald-500" />
                            {lead.decision_maker.name}
                          </span>
                          <span className="text-[11px] text-muted-foreground truncate">
                            {lead.decision_maker.title}
                          </span>
                          <span className="text-[11px] text-primary/80 font-mono">
                            {lead.decision_maker.email}
                          </span>
                        </div>
                      </TableCell>

                      <TableCell className="text-right pr-4">
                        <div className="flex items-center justify-end gap-1.5">
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() => setSelectedLead(lead)}
                            className="h-8 gap-1.5 text-xs font-medium"
                          >
                            <Mail className="h-3.5 w-3.5 text-primary" />
                            Voir Pitch
                          </Button>

                          <Button asChild size="sm" variant="ghost" className="h-8 px-2" title="Télécharger le rapport d'audit PDF">
                            <a href={getLeadPdfUrl(lead.id)} download>
                              <FileText className="h-4 w-4 text-muted-foreground hover:text-foreground" />
                            </a>
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Pitch Preview Modal */}
      <Dialog open={!!selectedLead} onOpenChange={(open) => !open && setSelectedLead(null)}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-base font-bold">
              <Mail className="h-5 w-5 text-primary" />
              Angle de Prospection Prêt à Envoyer
            </DialogTitle>
            <DialogDescription className="text-xs text-muted-foreground">
              Pitch rédigé sur-mesure pour {selectedLead?.decision_maker.name} ({selectedLead?.domain}) avec score {selectedLead?.score}/100.
            </DialogDescription>
          </DialogHeader>

          {selectedLead && (
            <div className="space-y-4 pt-2">
              <div className="rounded-lg border border-border/80 bg-muted/30 p-4 font-mono text-xs leading-relaxed whitespace-pre-wrap select-all">
                {selectedLead.pitch_email}
              </div>

              <div className="flex items-center justify-between gap-3 pt-2">
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-[11px] font-mono">
                    Destinataire : {selectedLead.decision_maker.email}
                  </Badge>
                  {selectedLead.decision_maker.linkedin_url && (
                    <a
                      href={selectedLead.decision_maker.linkedin_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs text-primary hover:underline flex items-center gap-0.5"
                    >
                      LinkedIn
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    onClick={() => handleCopyPitch(selectedLead.pitch_email)}
                    className="h-8 gap-1.5 text-xs font-semibold"
                  >
                    {copied ? (
                      <>
                        <Check className="h-3.5 w-3.5 text-emerald-400" />
                        Copié !
                      </>
                    ) : (
                      <>
                        <Copy className="h-3.5 w-3.5" />
                        Copier le Pitch
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
