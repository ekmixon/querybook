import { IAccessRequest } from 'const/accessRequest';
import type {
    IDataCell,
    IDataCellMeta,
    IDataDocEditor,
    IRawDataDoc,
} from 'const/datadoc';
import type {
    IDataDocScheduleKwargs,
    IDataDocTaskSchedule,
    ITaskStatusRecord,
} from 'const/schedule';

import dataDocSocket from 'lib/data-doc/datadoc-socketio';
import ds from 'lib/datasource';

export const DataDocResource = {
    getAll: (filterMode: string, environmentId: number) =>
        ds.fetch<IRawDataDoc[]>('/datadoc/', {
            filter_mode: filterMode,
            environment_id: environmentId,
        }),
    get: (docId: number) => ds.fetch<IRawDataDoc>(`/datadoc/${docId}/`),

    clone: (docId: number) => ds.save<IRawDataDoc>(`/datadoc/${docId}/clone/`),
    updateOwner: (docId: number, newOwnerId: number) =>
        ds.save<IDataDocEditor>(`/datadoc/${docId}/owner/`, {
            next_owner_id: newOwnerId,
            originator: dataDocSocket.socketId,
        }),

    create: (cells: Array<Partial<IDataCell>>, environmentId: number) =>
        ds.save<IRawDataDoc>('/datadoc/', {
            title: '',
            environment_id: environmentId,
            cells,
        }),

    createFromExecution: (
        environmentId: number,
        queryExecutionId: number,
        engineId: number,
        queryString: string
    ) =>
        ds.save<IRawDataDoc>('/datadoc/from_execution/', {
            title: '',
            environment_id: environmentId,
            execution_id: queryExecutionId,
            engine_id: engineId,
            query_string: queryString,
        }),

    update: (
        docId: number,
        fields: Partial<{
            public: boolean;
            archived: boolean;
            owner_uid: number;
            title: string;
            meta: Record<any, any>;
        }>
    ) => ds.update<IRawDataDoc>(`/datadoc/${docId}/`, fields),

    updateCell: (
        cellId: number,
        fields: Partial<{
            context: string;
            meta: IDataCellMeta;
        }>,
        sid?: string
    ) => {
        const params = { fields };
        if (sid != null) {
            params['sid'] = sid;
        }

        return ds.update<IDataCell>(`/data_cell/${cellId}/`, params);
    },

    delete: (docId: number) => ds.delete(`/datadoc/${docId}/`),

    favorite: (docId: number) =>
        ds.save<{
            id: number;
            data_doc_id: number;
            uid: number;
        }>(`/favorite_data_doc/${docId}/`),
    unfavorite: (docId: number) => ds.delete(`/favorite_data_doc/${docId}/`),
};

export const DataDocEditorResource = {
    get: (docId: number) =>
        ds.fetch<IDataDocEditor[]>(`/datadoc/${docId}/editor/`),
    create: (docId: number, uid: number, read: boolean, write: boolean) =>
        ds.save<IDataDocEditor>(`/datadoc/${docId}/editor/${uid}/`, {
            read,
            write,
            originator: dataDocSocket.socketId,
        }),

    update: (editorId: number, read: boolean, write: boolean) =>
        ds.update<IDataDocEditor>(`/datadoc_editor/${editorId}/`, {
            read,
            write,
            originator: dataDocSocket.socketId,
        }),

    delete: (editorId: number) =>
        ds.delete(`/datadoc_editor/${editorId}/`, {
            originator: dataDocSocket.socketId,
        }),
};

export const DataDocAccessRequestResource = {
    create: (docId: number) =>
        ds.save<IAccessRequest>(`/datadoc/${docId}/access_request/`, {
            originator: dataDocSocket.socketId,
        }),
    delete: (docId: number, uid: number) =>
        ds.delete(`/datadoc/${docId}/access_request/`, {
            uid,
            originator: dataDocSocket.socketId,
        }),
};

export const DataDocScheduleResource = {
    get: (docId: number) =>
        ds.fetch<IDataDocTaskSchedule>(`/datadoc/${docId}/schedule/`),
    create: (docId: number, cron: string, kwargs: IDataDocScheduleKwargs) =>
        ds.save<IDataDocTaskSchedule>(`/datadoc/${docId}/schedule/`, {
            cron,
            kwargs,
        }),
    update: (
        docId: number,
        params: {
            cron?: string;
            kwargs?: IDataDocScheduleKwargs;
            enabled?: boolean;
        }
    ) => ds.update<IDataDocTaskSchedule>(`/datadoc/${docId}/schedule/`, params),
    delete: (docId: number) => ds.delete(`/datadoc/${docId}/schedule/`),

    run: (docId: number) => ds.save<null>(`/datadoc/${docId}/schedule/run/`),
    getLogs: (docId: number) =>
        ds.fetch<ITaskStatusRecord[]>(`/datadoc/${docId}/schedule/logs/`),
};
