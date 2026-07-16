import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link2Off, Plus, Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { CopyButton } from "@/components/urls/CopyButton";
import { UrlFormDialog } from "@/components/urls/UrlFormDialog";
import { DeleteUrlDialog } from "@/components/urls/DeleteUrlDialog";
import { QrCodeDialog } from "@/components/urls/QrCodeDialog";
import { UrlRowActions } from "@/components/urls/UrlRowActions";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { urlsApi } from "@/lib/api";
import { formatDate } from "@/lib/date-utils";
import type { SortBy, SortOrder, Url } from "@/types/api";

const PAGE_SIZE = 10;

// Base UI's <Select.Value> doesn't auto-derive a label from the matching
// SelectItem the way Radix does — it just prints the raw value unless you
// give it a value -> label mapping function.
const SORT_LABELS: Record<string, string> = {
  "created_at:desc": "Newest first",
  "created_at:asc": "Oldest first",
  "click_count:desc": "Most clicked",
  "click_count:asc": "Least clicked",
};

export default function DashboardPage() {
  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const [sort, setSort] = useState<`${SortBy}:${SortOrder}`>("created_at:desc");
  const search = useDebouncedValue(searchInput, 350);
  const [sortBy, order] = sort.split(":") as [SortBy, SortOrder];

  const [formDialog, setFormDialog] = useState<{ open: boolean; url?: Url }>({ open: false });
  const [deleteDialog, setDeleteDialog] = useState<{ open: boolean; url: Url | null }>({
    open: false,
    url: null,
  });
  const [qrDialog, setQrDialog] = useState<{ open: boolean; url: Url | null }>({
    open: false,
    url: null,
  });

  const { data, isLoading, isPlaceholderData } = useQuery({
    queryKey: ["urls", { page, search, sortBy, order }],
    queryFn: () => urlsApi.list({ page, page_size: PAGE_SIZE, search: search || undefined, sort_by: sortBy, order }),
    placeholderData: (previous) => previous,
  });

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Your links</h1>
          <p className="text-sm text-muted-foreground">
            {data ? `${data.total} link${data.total === 1 ? "" : "s"} total` : "Loading..."}
          </p>
        </div>
        <Button onClick={() => setFormDialog({ open: true })}>
          <Plus />
          Create link
        </Button>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute top-1/2 left-2.5 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search by URL or short code..."
            className="pl-8"
            value={searchInput}
            onChange={(e) => {
              setSearchInput(e.target.value);
              setPage(1);
            }}
          />
        </div>
        <Select
          value={sort}
          onValueChange={(value) => {
            setSort(value as typeof sort);
            setPage(1);
          }}
        >
          <SelectTrigger className="w-full sm:w-56">
            <SelectValue>{(value: string) => SORT_LABELS[value] ?? value}</SelectValue>
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="created_at:desc">Newest first</SelectItem>
            <SelectItem value="created_at:asc">Oldest first</SelectItem>
            <SelectItem value="click_count:desc">Most clicked</SelectItem>
            <SelectItem value="click_count:asc">Least clicked</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      ) : !data || data.items.length === 0 ? (
        <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed py-16 text-center">
          <Link2Off className="h-8 w-8 text-muted-foreground" />
          <p className="font-medium">{search ? "No links match your search" : "No links yet"}</p>
          {!search && (
            <Button variant="outline" onClick={() => setFormDialog({ open: true })}>
              <Plus />
              Create your first link
            </Button>
          )}
        </div>
      ) : (
        <div className={isPlaceholderData ? "opacity-60 transition-opacity" : undefined}>
          <div className="rounded-lg border bg-background">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Short link</TableHead>
                  <TableHead>Destination</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Clicks</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-10" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.items.map((url) => (
                  <TableRow key={url.id}>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <a
                          href={url.short_url}
                          target="_blank"
                          rel="noreferrer"
                          className="font-medium text-foreground underline-offset-4 hover:underline"
                        >
                          {url.short_url.replace(/^https?:\/\//, "")}
                        </a>
                        <CopyButton value={url.short_url} />
                      </div>
                    </TableCell>
                    <TableCell className="max-w-64 truncate text-muted-foreground" title={url.original_url}>
                      {url.original_url}
                    </TableCell>
                    <TableCell className="text-muted-foreground">{formatDate(url.created_at)}</TableCell>
                    <TableCell className="text-right">{url.click_count.toLocaleString()}</TableCell>
                    <TableCell>
                      {url.is_expired ? (
                        <Badge variant="destructive">Expired</Badge>
                      ) : (
                        <Badge variant="secondary">Active</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <UrlRowActions
                        url={url}
                        onEdit={() => setFormDialog({ open: true, url })}
                        onDelete={() => setDeleteDialog({ open: true, url })}
                        onShowQr={() => setQrDialog({ open: true, url })}
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {totalPages > 1 && (
            <div className="mt-4 flex items-center justify-between text-sm text-muted-foreground">
              <span>
                Page {page} of {totalPages}
              </span>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </div>
      )}

      <UrlFormDialog
        open={formDialog.open}
        onOpenChange={(open) => setFormDialog((s) => ({ ...s, open }))}
        url={formDialog.url}
      />
      <DeleteUrlDialog
        open={deleteDialog.open}
        onOpenChange={(open) => setDeleteDialog((s) => ({ ...s, open }))}
        url={deleteDialog.url}
      />
      <QrCodeDialog
        open={qrDialog.open}
        onOpenChange={(open) => setQrDialog((s) => ({ ...s, open }))}
        url={qrDialog.url}
      />
    </div>
  );
}
