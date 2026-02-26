const { useState, useEffect, useMemo } = React;

const PAGE_SIZE = 10;
// Эндпоинт таблицы
const API_URL = '/api/tickets/table';

function valueOrNone(v) {
  if (v === null || v === undefined || v === '') {
    return 'None';
  }
  return v;
}

function formatDate(isoString) {
  if (!isoString) return 'None';
  const d = new Date(isoString);
  if (isNaN(d)) return 'None';
  const dd = String(d.getDate()).padStart(2, '0');
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const yyyy = d.getFullYear();
  return `${dd}.${mm}.${yyyy}`;
}

function formatToneLabel(sentiment) {
  if (!sentiment) return 'None';
  const lower = String(sentiment).toLowerCase();
  if (lower === 'позитивно') return 'Позитивно';
  if (lower === 'негативно') return 'Негативно';
  if (lower === 'нейтрально') return 'Нейтрально';
  return sentiment;
}

function toneClass(sentiment) {
  if (!sentiment) return '';
  const lower = String(sentiment).toLowerCase();
  if (lower === 'позитивно') return 'tone-positive';
  if (lower === 'негативно') return 'tone-negative';
  if (lower === 'нейтрально') return 'tone-neutral';
  return '';
}

function App() {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [filters, setFilters] = useState({
    status: 'all',
    search: '',
    dateFrom: '',
    dateTo: '',
  });

  const [currentPage, setCurrentPage] = useState(1);

  async function loadTickets() {
    try {
      setLoading(true);
      setError('');

      const params = new URLSearchParams();

      if (filters.status && filters.status !== 'all') {
        params.set('status', filters.status);
      }

      if (filters.dateFrom) {
        params.set('date_from', filters.dateFrom);
      }
      if (filters.dateTo) {
        params.set('date_to', filters.dateTo);
      }

      params.set('sort', 'date');
      params.set('dir', 'desc');

      const url = `${API_URL}?${params.toString()}`;

      const res = await fetch(url);
      if (!res.ok) throw new Error('Ошибка загрузки данных');

      const data = await res.json();
      setTickets(Array.isArray(data) ? data : []);
    } catch (e) {
      setError(e.message || 'Ошибка загрузки');
      setTickets([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadTickets();
  }, []);

  const filteredTickets = useMemo(() => {
    const dateFrom = filters.dateFrom ? new Date(filters.dateFrom) : null;
    const dateToRaw = filters.dateTo ? new Date(filters.dateTo) : null;
    let dateTo = null;
    if (dateToRaw) {
      dateTo = new Date(dateToRaw);
      dateTo.setDate(dateTo.getDate() + 1); // включительно
    }

    return tickets.filter((t) => {
      if (filters.status !== 'all' && t.status !== filters.status) {
        return false;
      }

      if (filters.search) {
        const s = filters.search.toLowerCase();
        const haystack = (
          (t.full_name || '') +
          ' ' +
          (t.email || '') +
          ' ' +
          (t.phone || '') +
          ' ' +
          (t.object_name || '') +
          ' ' +
          (t.issue_summary || '')
        ).toLowerCase();
        if (!haystack.includes(s)) return false;
      }

      if (t.date) {
        const created = new Date(t.date);
        if (dateFrom && created < dateFrom) return false;
        if (dateTo && created >= dateTo) return false;
      }

      return true;
    });
  }, [tickets, filters]);

  const totalPages = Math.max(
    1,
    Math.ceil(filteredTickets.length / PAGE_SIZE),
  );

  const pageTickets = useMemo(() => {
    const startIndex = (currentPage - 1) * PAGE_SIZE;
    return filteredTickets.slice(startIndex, startIndex + PAGE_SIZE);
  }, [filteredTickets, currentPage]);

  useEffect(() => {
    setCurrentPage(1);
  }, [filters]);

  function handleFilterChange(name, value) {
    setFilters((prev) => ({ ...prev, [name]: value }));
  }

  function changePage(delta) {
    setCurrentPage((prev) => {
      const next = prev + delta;
      if (next < 1 || next > totalPages) return prev;
      return next;
    });
  }

  function openChat(id) {
    window.location.href = `/chat.html?ticketId=${encodeURIComponent(id)}`;
  }

  function handleAddTicket() {
    window.location.href = '/new-ticket.html';
  }

  if (loading && tickets.length === 0) {
    return <div className="container">Загрузка...</div>;
  }

  const hasOriginalData = tickets && tickets.length > 0;

  return (
    <div className="container">
      {error && (
        <p style={{ color: '#b3261e', marginTop: 0, marginBottom: '12px' }}>
          Ошибка: {error}
        </p>
      )}

      <div className="page-title">
        <img
          src="/static/table.png"
          alt="Таблица"
          className="title-icon"
        />
        <h1>Обращения в поддержку</h1>
      </div>

      <div className="filters">
        <div className="filters-left">
          {/* селект статуса (значения поле status) */}
          <select
            value={filters.status}
            onChange={(e) => handleFilterChange('status', e.target.value)}
          >
            <option value="all">Все</option>
            <option value="new">Новые</option>
            <option value="in_progress">В работе</option>
            <option value="resolved">Решённые</option>
          </select>

          От

          <input
            type="date"
            placeholder="От"
            value={filters.dateFrom}
            onChange={(e) => handleFilterChange('dateFrom', e.target.value)}
          />

          До

          <input
            type="date"
            placeholder="До"
            value={filters.dateTo}
            onChange={(e) => handleFilterChange('dateTo', e.target.value)}
          />
        </div>

        <div className="filters-center">
          <input
            type="text"
            placeholder="Поиск..."
            value={filters.search}
            onChange={(e) => handleFilterChange('search', e.target.value)}
          />
        </div>

        <div className="actions-panel">
          <button
            className="primary-action"
            onClick={handleAddTicket}
          >
            Добавить запись
          </button>
          <button
            className="secondary-action"
            onClick={loadTickets}
            disabled={loading}
          >
            Обновить таблицу
          </button>
        </div>
      </div>

      <div className="table-wrapper">
        <table id="ticketsTable">
          <thead>
            <tr>
              <th>ID</th>
              <th>Дата</th>
              <th>ФИО</th>
              <th>Объект</th>
              <th>Телефон</th>
              <th>Email</th>
              <th>Заводские номера</th>
              <th>Тип приборов</th>
              <th>Тональность</th>
              <th>Суть вопроса</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            {!hasOriginalData ? (
              <tr>
                <td>None</td>
                <td>None</td>
                <td>None</td>
                <td>None</td>
                <td>None</td>
                <td>None</td>
                <td>None</td>
                <td>None</td>
                <td>None</td>
                <td>None</td>
                <td>None</td>
              </tr>
            ) : pageTickets.length === 0 ? (
              <tr>
                <td colSpan={11}>Нет данных по выбранным условиям</td>
              </tr>
            ) : (
              pageTickets.map((t, idx) => (
                <tr key={t.id ?? idx}>
                  <td>{valueOrNone(t.id)}</td>
                  <td>{formatDate(t.date)}</td>
                  <td>{valueOrNone(t.full_name)}</td>
                  <td>{valueOrNone(t.object_name)}</td>
                  <td>{valueOrNone(t.phone)}</td>
                  <td>{valueOrNone(t.email)}</td>
                  <td>{valueOrNone(t.serial_numbers)}</td>
                  <td>{valueOrNone(t.device_type)}</td>
                  <td className={`tone ${toneClass(t.sentiment)}`}>
                    {formatToneLabel(t.sentiment)}
                  </td>
                  <td>{valueOrNone(t.issue_summary)}</td>
                  <td className="actions">
                    <button
                      onClick={() => (t.id ? openChat(t.id) : null)}
                      disabled={!t.id}
                    >
                      Открыть
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="pagination">
        <button
          disabled={currentPage === 1}
          onClick={() => changePage(-1)}
        >
          Назад
        </button>
        <span>
          Страница {currentPage} из {totalPages}
        </span>
        <button
          disabled={currentPage === totalPages}
          onClick={() => changePage(1)}
        >
          Вперёд
        </button>
      </div>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);