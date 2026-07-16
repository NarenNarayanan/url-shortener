import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ArrowLeft, MousePointerClick, Monitor, Chrome, Smartphone } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { urlsApi } from "@/lib/api";
import type { AnalyticsGroupBy, BreakdownItem } from "@/types/api";

// Base UI's <Select.Value> doesn't auto-derive a label from the matching
// SelectItem the way Radix does — needs an explicit value -> label mapping.
const DAYS_LABELS: Record<string, string> = {
  "7": "Last 7 days",
  "30": "Last 30 days",
  "90": "Last 90 days",
  "365": "Last year",
};

const CHART_COLORS = [
  "var(--chart-1)",
  "var(--chart-2)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
];

function StatCard({ icon: Icon, label, value }: { icon: typeof MousePointerClick; label: string; value: string }) {
  return (
    <Card>
      <CardContent className="flex items-center gap-3 py-2">
        <div className="flex h-9 w-9 items-center justify-center rounded-md bg-muted">
          <Icon className="h-4 w-4 text-muted-foreground" />
        </div>
        <div>
          <p className="text-xs text-muted-foreground">{label}</p>
          <p className="font-medium">{value}</p>
        </div>
      </CardContent>
    </Card>
  );
}

function BreakdownChart({ title, data }: { title: string; data: BreakdownItem[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {data.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">No data yet</p>
        ) : (
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16 }}>
              <XAxis type="number" hide />
              <YAxis
                type="category"
                dataKey="label"
                width={90}
                tickLine={false}
                axisLine={false}
                tick={{ fontSize: 12 }}
              />
              <Tooltip
                cursor={{ fill: "var(--muted)" }}
                contentStyle={{
                  background: "var(--popover)",
                  border: "1px solid var(--border)",
                  borderRadius: "var(--radius)",
                  fontSize: 12,
                }}
              />
              <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                {data.map((_, index) => (
                  <Cell key={index} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}

export default function AnalyticsPage() {
  const { shortCode } = useParams<{ shortCode: string }>();
  const [days, setDays] = useState(30);
  const [groupBy, setGroupBy] = useState<AnalyticsGroupBy>("day");

  const { data, isLoading, isError } = useQuery({
    queryKey: ["analytics", shortCode, days, groupBy],
    queryFn: () => urlsApi.analytics(shortCode!, days, groupBy),
    enabled: Boolean(shortCode),
  });

  if (isError) {
    return (
      <div className="space-y-4">
        <Link to="/dashboard" className="flex w-fit items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" />
          Back to dashboard
        </Link>
        <p className="text-muted-foreground">This link doesn&apos;t exist or isn&apos;t yours.</p>
      </div>
    );
  }

  const topBrowser = data?.by_browser[0]?.label ?? "—";
  const topOs = data?.by_os[0]?.label ?? "—";
  const topDevice = data?.by_device_type[0]?.label ?? "—";

  const timeSeriesData =
    data?.clicks_over_time.map((bucket) => ({
      period: new Date(bucket.period).toLocaleDateString(undefined, { month: "short", day: "numeric" }),
      count: bucket.count,
    })) ?? [];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <Link
            to="/dashboard"
            className="flex w-fit items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to dashboard
          </Link>
          <h1 className="mt-1 text-2xl font-semibold">/{shortCode}</h1>
        </div>

        <div className="flex items-center gap-2">
          <Tabs value={groupBy} onValueChange={(value) => setGroupBy(value as AnalyticsGroupBy)}>
            <TabsList>
              <TabsTrigger value="day">Daily</TabsTrigger>
              <TabsTrigger value="week">Weekly</TabsTrigger>
            </TabsList>
          </Tabs>
          <Select value={String(days)} onValueChange={(value) => setDays(Number(value))}>
            <SelectTrigger className="w-32">
              <SelectValue>{(value: string) => DAYS_LABELS[value] ?? value}</SelectValue>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7">Last 7 days</SelectItem>
              <SelectItem value="30">Last 30 days</SelectItem>
              <SelectItem value="90">Last 90 days</SelectItem>
              <SelectItem value="365">Last year</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {isLoading || !data ? (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-16" />
            ))}
          </div>
          <Skeleton className="h-64 w-full" />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <StatCard icon={MousePointerClick} label="Total clicks" value={data.total_clicks.toLocaleString()} />
            <StatCard icon={Chrome} label="Top browser" value={topBrowser} />
            <StatCard icon={Monitor} label="Top OS" value={topOs} />
            <StatCard icon={Smartphone} label="Top device" value={topDevice} />
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Clicks over time</CardTitle>
            </CardHeader>
            <CardContent>
              {timeSeriesData.length === 0 ? (
                <p className="py-16 text-center text-sm text-muted-foreground">No clicks in this period</p>
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <AreaChart data={timeSeriesData} margin={{ left: -16 }}>
                    <defs>
                      <linearGradient id="clicksGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="var(--chart-1)" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="var(--chart-1)" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
                    <XAxis dataKey="period" tickLine={false} axisLine={false} tick={{ fontSize: 12 }} />
                    <YAxis allowDecimals={false} tickLine={false} axisLine={false} tick={{ fontSize: 12 }} />
                    <Tooltip
                      contentStyle={{
                        background: "var(--popover)",
                        border: "1px solid var(--border)",
                        borderRadius: "var(--radius)",
                        fontSize: 12,
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="count"
                      stroke="var(--chart-1)"
                      strokeWidth={2}
                      fill="url(#clicksGradient)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>

          <div className="grid gap-4 md:grid-cols-3">
            <BreakdownChart title="Browser" data={data.by_browser} />
            <BreakdownChart title="Operating system" data={data.by_os} />
            <BreakdownChart title="Device type" data={data.by_device_type} />
          </div>
        </>
      )}
    </div>
  );
}
