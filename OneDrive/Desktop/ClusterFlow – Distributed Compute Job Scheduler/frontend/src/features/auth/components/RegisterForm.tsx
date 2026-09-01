import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { Button } from '../../../components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';

interface RegisterFormProps {
  onSuccess: () => void;
  onToggleForm: () => void;
}

export const RegisterForm: React.FC<RegisterFormProps> = ({ onSuccess, onToggleForm }) => {
  const { register, isLoading, error } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await register({ email, password });
      onSuccess();
    } catch (err) {
      // Error handled by hook
    }
  };

  return (
    <Card className="w-full max-w-md mx-auto bg-card/60 backdrop-blur-md border-t-4 border-t-primary shadow-xl">
      <CardHeader>
        <CardTitle className="text-2xl text-center font-bold tracking-tight text-foreground">
          Create Operator Account
        </CardTitle>
      </CardHeader>
      <CardContent>
        {error && (
          <div className="mb-4 p-3 rounded bg-red-900/30 border border-destructive/20 text-destructive text-xs">
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">
              Email Address
            </label>
            <input
              type="email"
              className="form-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="operator@clusterflow.io"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">
              Access Password
            </label>
            <input
              type="password"
              className="form-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Min 6 characters"
              required
            />
          </div>
          <Button type="submit" variant="primary" className="w-full mt-6" isLoading={isLoading}>
            Provision Operator Role
          </Button>
        </form>

        <div className="mt-6 text-center text-xs text-muted-foreground">
          Already registered?{' '}
          <button onClick={onToggleForm} className="text-primary hover:text-primary font-medium">
            Authenticate Operator
          </button>
        </div>
      </CardContent>
    </Card>
  );
};
