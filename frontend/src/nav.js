import { ROLES } from './constants.js'

const [ADMIN, QA, TECH] = ROLES

// Who may open a page. A page that is not listed is open to everyone who is logged in.
export const ROUTE_ROLES = {
  'sample/create': [ADMIN, TECH], 'sample/change': [ADMIN, TECH], 'sample/delete': [ADMIN], sap: [ADMIN],
  receipt: [ADMIN, TECH], allocation: [ADMIN], observation: [ADMIN, QA, TECH], testing: [ADMIN, QA], review: [ADMIN],
  'product/create': [ADMIN], 'product/change': [ADMIN], users: [ADMIN],
}
export const allowed = (route, role) => !ROUTE_ROLES[route] || ROUTE_ROLES[route].includes(role)

// [label, route] pairs. "sample/create" = page "sample", mode "create".
export const TREE = [
  { title: 'Transactions', items: [
    { label: 'Sample Login', kids: [['Create', 'sample/create'], ['Change', 'sample/change'],
      ['Delete/Cancel', 'sample/delete'], ['Display', 'sample/display'], ['Receipt From SAP', 'sap']] },
    ['Sample Receipt', 'receipt'], ['Work Allocation', 'allocation'], ['Observation Entry', 'observation'],
    ['Sample Testing', 'testing'], ['Review & Approve', 'review'], ['Sample Query', 'query']] },
  { title: 'Master Files', items: [
    { label: 'Product/Material Master', kids: [['Create', 'product/create'], ['Change', 'product/change'],
      ['Display', 'product/display'], ['List', 'product/list']] },
    ['Party Master', 'party'], ['Test Characteristics', 'test'], ['Miscellaneous', 'misc'],
    ['Assay Master', 'assay'], ['Sampling Inspection', 'sampling']] },
  { title: 'Specifications', items: [['Specification Master', 'spec']] },
]

export const flat = t => t.items.flatMap(i => Array.isArray(i) ? [i] : i.kids.map(k => [`${i.label} - ${k[0]}`, k[1]]))
const sec = n => flat(TREE.find(t => t.title === n))

export const MENUS = {
  System: [['Home', 'home'], ['User Management', 'users'], ['Change password', '#password'],
    ['Toggle dark mode', '#theme'], ['Sign out', '#logout']],
  'Master Files': sec('Master Files'), Specifications: sec('Specifications'), Transactions: sec('Transactions'),
  Review: [['Review & Approve', 'review']], Print: [['Print Sample Report', 'query']], Query: [['Sample Query', 'query']],
  Addons: [['Addons', 'soon/Addons']], QMS: [['QMS', 'soon/QMS']], STP: [['STP', 'soon/STP']],
  Help: [['About PharmaLIMS', '#about']],
}

export const TITLES = { home: 'Home', users: 'User Management', 'soon/Addons': 'Addons', 'soon/QMS': 'QMS', 'soon/STP': 'STP' }
TREE.forEach(t => flat(t).forEach(([l, r]) => { TITLES[r] = l }))
