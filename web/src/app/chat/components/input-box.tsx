// Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
// SPDX-License-Identifier: MIT

import { AnimatePresence, motion } from "framer-motion";
import { ArrowUp, X, FileText, AlertTriangle, Hash, MessageSquare, ChevronsUpDown, Code } from "lucide-react";
import {
  type KeyboardEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import { Detective } from "~/components/deer-flow/icons/detective";
import { Tooltip } from "~/components/deer-flow/tooltip";
import { Button } from "~/components/ui/button";
import type { CppCheckData, Option } from "~/core/messages";
import {
  setEnableBackgroundInvestigation,
  useSettingsStore,
} from "~/core/store";
import { cn } from "~/lib/utils";
import { Input } from "~/components/ui/input";
import { Label } from "~/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "~/components/ui/select";

export function InputBox({
  className,
  size,
  responding,
  feedback,
  onSend,
  onSendCppCheck,
  onCancel,
  onRemoveFeedback,
}: {
  className?: string;
  size?: "large" | "normal";
  responding?: boolean;
  feedback?: { option: Option } | null;
  onSend?: (message: string, options?: { interruptFeedback?: string }) => void;
  onSendCppCheck?: (data: CppCheckData) => void;
  onCancel?: () => void;
  onRemoveFeedback?: () => void;
}) {
  const [message, setMessage] = useState("");
  const [imeStatus, setImeStatus] = useState<"active" | "inactive">("inactive");
  const [indent, setIndent] = useState(0);
  const [inputMode, setInputMode] = useState<"text" | "cppcheck">("text");
  const [cppCheckData, setCppCheckData] = useState<CppCheckData>({
    file: "",
    line: "",
    severity: "warning",
    id: "",
    summary: "",
  });
  const backgroundInvestigation = useSettingsStore(
    (state) => state.general.enableBackgroundInvestigation,
  );
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const feedbackRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (feedback) {
      setMessage("");

      setTimeout(() => {
        if (feedbackRef.current) {
          setIndent(feedbackRef.current.offsetWidth);
        }
      }, 200);
    }
    setTimeout(() => {
      textareaRef.current?.focus();
    }, 0);
  }, [feedback]);

  const handleSendMessage = useCallback(() => {
    if (responding) {
      onCancel?.();
    } else {
      if (inputMode === "text") {
        if (message.trim() === "") {
          return;
        }
        if (onSend) {
          onSend(message, {
            interruptFeedback: feedback?.option.value,
          });
          setMessage("");
          onRemoveFeedback?.();
        }
      } else {
        if (cppCheckData.file.trim() === "" || cppCheckData.line.trim() === "") {
          console.warn("File and Line are required for CppCheck input.");
          return;
        }
        if (onSendCppCheck) {
          onSendCppCheck(cppCheckData);
          setCppCheckData({ file: "", line: "", severity: "warning", id: "", summary: "" });
          setInputMode("text"); // Reset to text mode after sending
          onRemoveFeedback?.();
        } else if (onSend) {
          // Fallback to regular send if the cppcheck handler isn't provided
          const cppCheckMessage = `CppCheck Input:
File: ${cppCheckData.file}
Line: ${cppCheckData.line}
Severity: ${cppCheckData.severity}
Id: ${cppCheckData.id}
Summary: ${cppCheckData.summary}`;
          onSend(cppCheckMessage, {
            interruptFeedback: feedback?.option.value,
          });
          setCppCheckData({ file: "", line: "", severity: "warning", id: "", summary: "" });
          setInputMode("text"); // Reset to text mode after sending
          onRemoveFeedback?.();
        }
      }
    }
  }, [responding, onCancel, message, onSend, onSendCppCheck, feedback, onRemoveFeedback, inputMode, cppCheckData]);

  const handleKeyDown = useCallback(
    (event: KeyboardEvent<HTMLTextAreaElement>) => {
      if (responding) {
        return;
      }
      if (
        event.key === "Enter" &&
        !event.shiftKey &&
        !event.metaKey &&
        !event.ctrlKey &&
        imeStatus === "inactive"
      ) {
        event.preventDefault();
        handleSendMessage();
      }
    },
    [responding, imeStatus, handleSendMessage],
  );

  const handleCppCheckDataChange = useCallback((field: keyof CppCheckData, value: string) => {
    setCppCheckData(prev => ({ ...prev, [field]: value }));
  }, []);

  const toggleInputMode = useCallback(() => {
    setInputMode(prev => prev === "text" ? "cppcheck" : "text");
  }, []);

  return (
    <div className={cn("bg-card relative rounded-[24px] border", className)}>
      {inputMode === "cppcheck" && (
        <motion.div
          className="grid grid-cols-2 gap-x-4 gap-y-3 p-4 border-b"
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          transition={{ duration: 0.3, ease: "easeInOut" }}
        >
          <div>
            <Label htmlFor="cppcheck-file" className="text-xs font-medium text-muted-foreground">File Path</Label>
            <div className="flex items-center gap-2 mt-1">
              <FileText size={16} className="text-muted-foreground" />
              <Input
                id="cppcheck-file"
                placeholder="e.g., src/utils/helpers.c"
                value={cppCheckData.file}
                onChange={(e) => handleCppCheckDataChange("file", e.target.value)}
                className="h-8 text-sm"
              />
            </div>
          </div>
          <div>
            <Label htmlFor="cppcheck-line" className="text-xs font-medium text-muted-foreground">Line Number</Label>
            <div className="flex items-center gap-2 mt-1">
              <Hash size={16} className="text-muted-foreground" />
              <Input
                id="cppcheck-line"
                type="number"
                placeholder="e.g., 42"
                value={cppCheckData.line}
                onChange={(e) => handleCppCheckDataChange("line", e.target.value)}
                className="h-8 text-sm"
              />
            </div>
          </div>
          <div>
            <Label htmlFor="cppcheck-severity" className="text-xs font-medium text-muted-foreground">Severity</Label>
            <div className="flex items-center gap-2 mt-1">
              <AlertTriangle size={16} className="text-muted-foreground" />
              <Select 
                value={cppCheckData.severity} 
                onValueChange={(value) => handleCppCheckDataChange("severity", value)}
              >
                <SelectTrigger className="h-8 text-sm">
                  <SelectValue placeholder="Select severity" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="error">Error</SelectItem>
                  <SelectItem value="warning">Warning</SelectItem>
                  <SelectItem value="style">Style</SelectItem>
                  <SelectItem value="performance">Performance</SelectItem>
                  <SelectItem value="information">Information</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div>
            <Label htmlFor="cppcheck-id" className="text-xs font-medium text-muted-foreground">Defect ID</Label>
            <div className="flex items-center gap-2 mt-1">
              <MessageSquare size={16} className="text-muted-foreground" />
              <Input
                id="cppcheck-id"
                placeholder="e.g., nullPointer"
                value={cppCheckData.id}
                onChange={(e) => handleCppCheckDataChange("id", e.target.value)}
                className="h-8 text-sm"
              />
            </div>
          </div>
          <div className="col-span-2">
            <Label htmlFor="cppcheck-summary" className="text-xs font-medium text-muted-foreground">Summary</Label>
            <div className="flex items-center gap-2 mt-1">
              <FileText size={16} className="text-muted-foreground" />
              <Input
                id="cppcheck-summary"
                placeholder="e.g., Null pointer dereference"
                value={cppCheckData.summary}
                onChange={(e) => handleCppCheckDataChange("summary", e.target.value)}
                className="h-8 text-sm"
              />
            </div>
          </div>
        </motion.div>
      )}

      <AnimatePresence>
        {feedback && (
          <div
            ref={feedbackRef}
            className="absolute top-0 left-0 z-0 origin-bottom-left px-4 pt-3"
          >
            <div className="bg-cyan-500/10 flex max-w-[200px] items-center gap-1 overflow-hidden rounded-md px-2 py-1.5">
              <div className="flex-1 truncate">{feedback.option.text}</div>
              <button
                type="button"
                className="flex-shrink-0 text-muted-foreground focus:text-foreground hover:text-foreground"
                onClick={onRemoveFeedback}
              >
                <X className="size-4" />
              </button>
            </div>
          </div>
        )}
      </AnimatePresence>

      <div className="flex px-4">
        <div
          className={cn(
            "relative flex w-full gap-1 py-3",
            feedback && "origin-bottom-right",
          )}
          style={{
            paddingLeft: feedback && indent ? indent + 4 : 0,
          }}
        >
          <Tooltip
            open={backgroundInvestigation}
            title={
              backgroundInvestigation
                ? "Web search is enabled"
                : "Web search is disabled"
            }
          >
            <Button
              variant="ghost"
              className={cn(
                "size-fit cursor-pointer rounded-full px-2",
                backgroundInvestigation &&
                  (responding ? "text-cyan-700" : "text-cyan-500"),
                !backgroundInvestigation && "text-muted-foreground",
              )}
              disabled={responding}
              onClick={() => {
                setEnableBackgroundInvestigation(!backgroundInvestigation);
              }}
            >
              <Detective className="size-5" />
            </Button>
          </Tooltip>

          <Tooltip
            title={inputMode === "text" ? "Switch to CppCheck Input" : "Switch to Text Input"}
          >
            <Button
              variant="ghost"
              className={cn(
                "size-fit cursor-pointer rounded-full px-2",
                inputMode === "cppcheck" ? "text-cyan-500" : "text-muted-foreground"
              )}
              disabled={responding}
              onClick={toggleInputMode}
            >
              <Code className="size-5" />
            </Button>
          </Tooltip>

          {inputMode === "text" ? (
            <textarea
              ref={textareaRef}
              className={cn(
                "flex-1 resize-none bg-transparent px-1 focus:outline-none",
                size === "large" && "text-xl",
              )}
              rows={1}
              style={{
                height: "1.5rem",
              }}
              placeholder={
                responding
                  ? "DeerFlow is responding..."
                  : "Ask me anything..."
              }
              value={message}
              onChange={(evt) => {
                setMessage(evt.target.value);

                // Adjust the textarea height based on content
                const target = evt.target;
                target.style.height = "1.5rem";
                target.style.height = `${target.scrollHeight}px`;
              }}
              onKeyDown={handleKeyDown}
              onCompositionStart={() => setImeStatus("active")}
              onCompositionEnd={() => setImeStatus("inactive")}
              disabled={responding}
            />
          ) : (
            <div className="flex-1 px-1 text-muted-foreground text-sm flex items-center">
              {cppCheckData.file && cppCheckData.line ? `${cppCheckData.file}:${cppCheckData.line}` : "Configure CppCheck Input..."}
            </div>
          )}

          <Button
            variant="ghost"
            className={cn(
              "size-fit cursor-pointer rounded-full px-2",
              responding && "text-muted-foreground hover:text-destructive",
              !responding && "text-cyan-500 hover:text-cyan-400",
            )}
            aria-label={responding ? "Cancel" : "Send"}
            onClick={handleSendMessage}
          >
            {responding ? (
              <X className="size-5" />
            ) : (
              <ArrowUp className="size-5" />
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
