import React, { useState } from 'react';
import { Job, Task } from '../../../types';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';

interface SubmitJobModalProps {
  onClose: () => void;
  onSubmit: (job: Job) => Promise<any>;
}

export const SubmitJobModal: React.FC<SubmitJobModalProps> = ({ onClose, onSubmit }) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState(5);
  const [envVars, setEnvVars] = useState<[string, string][]>([['', '']]);
  const [tasks, setTasks] = useState<{ name: string; command: string }[]>([{ name: '', command: '' }]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAddEnv = () => setEnvVars([...envVars, ['', '']]);
  const handleRemoveEnv = (i: number) => setEnvVars(envVars.filter((_, idx) => idx !== i));
  const handleEnvChange = (i: number, key: 0 | 1, val: string) => {
    const updated = [...envVars];
    updated[i][key] = val;
    setEnvVars(updated);
  };

  const handleAddTask = () => setTasks([...tasks, { name: '', command: '' }]);
  const handleRemoveTask = (i: number) => setTasks(tasks.filter((_, idx) => idx !== i));
  const handleTaskChange = (i: number, field: 'name' | 'command', val: string) => {
    const updated = [...tasks];
    updated[i][field] = val;
    setTasks(updated);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    // Map fields
    const variables: Record<string, string> = {};
    envVars.forEach(([k, v]) => {
      if (k.trim()) variables[k.trim()] = v.trim();
    });

    const jobTasks: Task[] = tasks.map((t, idx) => ({
      id: `task-${idx + 1}`,
      name: t.name.trim() || `Task #${idx + 1}`,
      command: t.command.trim(),
      state: 'PENDING',
      dependsOn: [],
      exitCode: 0,
    }));

    if (jobTasks.some(t => !t.command)) {
      setError('Each task requires an execution command');
      setIsSubmitting(false);
      return;
    }

    const payload: Job = {
      name: name.trim(),
      description: description.trim(),
      priority,
      state: 'PENDING',
      variables,
      tasks: jobTasks,
    };

    try {
      await onSubmit(payload);
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to submit compute request');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
      <Card className="w-full max-w-2xl">
        <CardHeader>
          <CardTitle>Submit Compute Job Flow</CardTitle>
          <Button variant="outline" className="px-2 py-1 h-8 text-xs" onClick={onClose}>✕</Button>
        </CardHeader>
        <CardContent className="max-h-[75vh] overflow-y-auto">
          {error && (
            <div className="mb-4 p-3 rounded bg-red-900/30 border border-destructive/20 text-destructive text-xs">
              {error}
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">Job Name</label>
                <input
                  type="text"
                  className="form-input"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="DeepLearning-Epochs-200"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">Priority (1 - 10)</label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  className="form-input"
                  value={priority}
                  onChange={(e) => setPriority(parseInt(e.target.value))}
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">Description</label>
              <textarea
                className="form-input h-20 resize-none"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Brief summary of the compute job..."
              />
            </div>

            {/* Variable Rows */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Environment Variables</label>
                <Button type="button" variant="outline" className="h-6 px-2 text-xs" onClick={handleAddEnv}>+ Add Var</Button>
              </div>
              <div className="space-y-2">
                {envVars.map((env, idx) => (
                  <div key={idx} className="flex gap-2">
                    <input
                      type="text"
                      placeholder="KEY"
                      className="form-input text-xs"
                      value={env[0]}
                      onChange={(e) => handleEnvChange(idx, 0, e.target.value)}
                    />
                    <input
                      type="text"
                      placeholder="VALUE"
                      className="form-input text-xs"
                      value={env[1]}
                      onChange={(e) => handleEnvChange(idx, 1, e.target.value)}
                    />
                    <Button type="button" variant="outline" className="h-9 px-3 text-destructive text-xs" onClick={() => handleRemoveEnv(idx)}>✕</Button>
                  </div>
                ))}
              </div>
            </div>

            {/* Tasks rows */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Execution Tasks</label>
                <Button type="button" variant="outline" className="h-6 px-2 text-xs" onClick={handleAddTask}>+ Add Task</Button>
              </div>
              <div className="space-y-3">
                {tasks.map((task, idx) => (
                  <div key={idx} className="flex gap-2 items-center bg-background/20 p-3 rounded border border-border">
                    <div className="flex-1 space-y-2">
                      <input
                        type="text"
                        placeholder="Task Name (e.g. data-download)"
                        className="form-input text-xs"
                        value={task.name}
                        onChange={(e) => handleTaskChange(idx, 'name', e.target.value)}
                        required
                      />
                      <input
                        type="text"
                        placeholder="Shell Command (e.g. python train.py --epochs 200)"
                        className="form-input text-xs font-mono"
                        value={task.command}
                        onChange={(e) => handleTaskChange(idx, 'command', e.target.value)}
                        required
                      />
                    </div>
                    {tasks.length > 1 && (
                      <Button type="button" variant="outline" className="h-9 px-3 text-destructive text-xs" onClick={() => handleRemoveTask(idx)}>✕</Button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6 border-t border-border pt-4">
              <Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
              <Button type="submit" variant="primary" isLoading={isSubmitting}>Submit Job</Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};
