import api from '../../../services/api';
import { Credentials, TokenResponse } from '../../../types';

export const authApi = {
  login: async (creds: Credentials): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/auth/login', creds);
    return response.data;
  },
  register: async (creds: Credentials): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/auth/register', creds);
    return response.data;
  },
};
